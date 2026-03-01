using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace CustomMod.Features;

/// <summary>
/// Canvas-based SickoMenu-style UI. Plain C# class (not MonoBehaviour).
/// Uses ScreenSpace-Overlay Canvas with manual mouse hit detection.
/// </summary>
public class HackMenuUI
{
    // ── Colors ──
    static readonly Color WinBg      = new(0.06f, 0.06f, 0.12f, 0.96f);
    static readonly Color TitleBg    = new(0.14f, 0.06f, 0.06f, 1f);
    static readonly Color TabDef     = new(0.10f, 0.10f, 0.18f, 0.95f);
    static readonly Color TabActive  = new(0.50f, 0.15f, 0.15f, 0.95f);
    static readonly Color TabHover   = new(0.28f, 0.12f, 0.12f, 0.95f);
    static readonly Color RowDef     = new(0.08f, 0.08f, 0.14f, 0.90f);
    static readonly Color RowHover   = new(0.18f, 0.10f, 0.10f, 0.95f);
    static readonly Color RowAction  = new(0.10f, 0.08f, 0.16f, 0.90f);
    static readonly Color OnColor    = new(0.1f, 0.85f, 0.1f, 1f);
    static readonly Color OffColor   = new(0.7f, 0.2f, 0.2f, 1f);
    static readonly Color AccentRed  = new(1f, 0.42f, 0.42f, 1f);
    static readonly Color TextWhite  = new(0.93f, 0.93f, 0.95f, 1f);
    static readonly Color TextDim    = new(0.55f, 0.55f, 0.65f, 1f);

    // ── Layout Constants ──
    const float WIN_W = 420f, WIN_H = 520f;
    const float TITLE_H = 30f, TAB_H = 26f, TAB_ROWS = 2f;
    const float ROW_H = 28f, ROW_GAP = 2f, ROW_PAD = 4f;
    const float CONTENT_TOP = TITLE_H + TAB_H * TAB_ROWS + 8f;

    // ── Root Objects ──
    private GameObject _rootGo;
    private RectTransform _canvasRect;
    private RectTransform _windowRect;
    private RectTransform _titleBarRect;
    private RectTransform _contentRect;
    private RectTransform _viewportRect;
    private GameObject _contentGo;
    private bool _built = false;

    // ── State ──
    private int _currentTab = 0;
    private bool _isDragging = false;
    private Vector2 _dragOffset;
    private float _scrollY = 0f;
    private float _maxScrollY = 0f;

    // ── Interactive Elements ──
    private List<UIBtn> _tabBtns = new();
    private List<UIBtn> _rows = new();
    private UIBtn _closeBtn;

    // ── Font Cache ──
    private static TMPro.TMP_FontAsset _font;

    private struct UIBtn
    {
        public RectTransform Rect;
        public Image Bg;
        public TMPro.TextMeshProUGUI Label;
        public Action OnClick;
        public Func<string> GetText;
        public Color DefaultColor;
        public bool IsHovered;
    }

    // ═══════════════════════════════════════
    //  PUBLIC API
    // ═══════════════════════════════════════

    public void EnsureBuilt()
    {
        if (_built && _rootGo != null) return;
        if (GetFont() == null) return; // Need font from game scene
        Build();
    }

    public void SetVisible(bool v)
    {
        if (_rootGo != null) _rootGo.SetActive(v);
    }

    public void HandleInput()
    {
        if (_rootGo == null || !_rootGo.activeSelf) return;

        Vector2 mouse = UnityEngine.Input.mousePosition;
        bool clicked = UnityEngine.Input.GetMouseButtonDown(0);
        bool held = UnityEngine.Input.GetMouseButton(0);

        // Drag
        HandleDrag(mouse, clicked, held);

        // Close button
        if (_closeBtn.Rect != null)
        {
            bool hover = HitTest(_closeBtn.Rect, mouse);
            UpdateHover(ref _closeBtn, hover);
            if (hover && clicked) { _closeBtn.OnClick?.Invoke(); return; }
        }

        // Tab buttons
        for (int i = 0; i < _tabBtns.Count; i++)
        {
            var btn = _tabBtns[i];
            bool hover = HitTest(btn.Rect, mouse);
            if (i == _currentTab)
            {
                if (btn.Bg != null) btn.Bg.color = TabActive;
            }
            else
            {
                UpdateHover(ref btn, hover);
            }
            _tabBtns[i] = btn;
            if (hover && clicked)
            {
                _currentTab = i;
                _scrollY = 0f;
                RebuildContent();
                break;
            }
        }

        // Content rows
        for (int i = 0; i < _rows.Count; i++)
        {
            var row = _rows[i];
            if (row.Rect == null || row.OnClick == null) continue;
            bool hover = HitTest(row.Rect, mouse) && HitTest(_viewportRect, mouse);
            UpdateHover(ref row, hover);
            _rows[i] = row;
            if (hover && clicked)
            {
                row.OnClick();
                RebuildContent();
                break;
            }
        }

        // Scroll
        HandleScroll(mouse);

        // Update dynamic text
        for (int i = 0; i < _rows.Count; i++)
        {
            var row = _rows[i];
            if (row.Label != null && row.GetText != null)
                try { row.Label.text = row.GetText(); } catch { }
        }
    }

    public void SwitchTab(int tab)
    {
        _currentTab = tab;
        _scrollY = 0f;
        if (_built) RebuildContent();
    }

    // ═══════════════════════════════════════
    //  BUILD UI
    // ═══════════════════════════════════════

    private void Build()
    {
        if (_rootGo != null) UnityEngine.Object.Destroy(_rootGo);

        // Root + Canvas
        _rootGo = new GameObject("PebblefordMenu");
        _rootGo.hideFlags = HideFlags.HideAndDontSave;
        UnityEngine.Object.DontDestroyOnLoad(_rootGo);

        var canvas = _rootGo.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 32000;

        var scaler = _rootGo.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.matchWidthOrHeight = 0.5f;

        _canvasRect = _rootGo.GetComponent<RectTransform>();

        // Window panel
        var winGo = MakeUIObj("Window", _rootGo);
        _windowRect = winGo.GetComponent<RectTransform>();
        _windowRect.sizeDelta = new Vector2(WIN_W, WIN_H);
        _windowRect.anchoredPosition = new Vector2(0, 0);
        var winImg = winGo.AddComponent<Image>();
        winImg.color = WinBg;

        // Title bar
        var titleGo = MakeUIObj("TitleBar", winGo);
        _titleBarRect = titleGo.GetComponent<RectTransform>();
        AnchorTop(_titleBarRect, 0, WIN_W, TITLE_H);
        var titleImg = titleGo.AddComponent<Image>();
        titleImg.color = TitleBg;

        // Title text
        var titleTxt = MakeText(titleGo, "PEBBLEFORD'S MENU", 14, TextWhite, TMPro.TextAlignmentOptions.Left);
        var ttRect = titleTxt.GetComponent<RectTransform>();
        ttRect.anchorMin = new Vector2(0, 0); ttRect.anchorMax = new Vector2(1, 1);
        ttRect.offsetMin = new Vector2(10, 0); ttRect.offsetMax = new Vector2(-30, 0);

        // Close button
        var closeGo = MakeUIObj("CloseBtn", titleGo);
        var closeRect = closeGo.GetComponent<RectTransform>();
        closeRect.anchorMin = new Vector2(1, 0); closeRect.anchorMax = new Vector2(1, 1);
        closeRect.offsetMin = new Vector2(-28, 2); closeRect.offsetMax = new Vector2(-2, -2);
        var closeBg = closeGo.AddComponent<Image>();
        closeBg.color = new Color(0.6f, 0.15f, 0.15f, 0.9f);
        var closeTxt = MakeText(closeGo, "X", 13, TextWhite, TMPro.TextAlignmentOptions.Center);
        FillParent(closeTxt.GetComponent<RectTransform>());

        _closeBtn = new UIBtn
        {
            Rect = closeRect, Bg = closeBg, Label = closeTxt,
            OnClick = () => { HackMenu.ShowMenu = false; SetVisible(false); },
            DefaultColor = new Color(0.6f, 0.15f, 0.15f, 0.9f)
        };

        // Tab bar
        BuildTabs(winGo);

        // Content area (scrollable)
        BuildContentArea(winGo);

        RebuildContent();
        _built = true;
    }

    private void BuildTabs(GameObject parent)
    {
        _tabBtns.Clear();
        string[] names = { "Vision", "Move", "Combat", "Troll", "Game", "Player", "Teleport", "Chat", "Cosmetics", "Doors" };
        int perRow = 5;
        float tabW = (WIN_W - 4f) / perRow;

        for (int i = 0; i < names.Length; i++)
        {
            int row = i / perRow;
            int col = i % perRow;
            float x = 2f + col * tabW;
            float y = TITLE_H + row * TAB_H;

            var go = MakeUIObj("Tab_" + names[i], parent);
            var rect = go.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0, 1);
            rect.anchorMax = new Vector2(0, 1);
            rect.pivot = new Vector2(0, 1);
            rect.anchoredPosition = new Vector2(x, -y);
            rect.sizeDelta = new Vector2(tabW - 1f, TAB_H - 1f);

            var bg = go.AddComponent<Image>();
            bg.color = i == 0 ? TabActive : TabDef;

            var txt = MakeText(go, names[i], 11, TextWhite, TMPro.TextAlignmentOptions.Center);
            FillParent(txt.GetComponent<RectTransform>());

            _tabBtns.Add(new UIBtn
            {
                Rect = rect, Bg = bg, Label = txt,
                DefaultColor = TabDef
            });
        }
    }

    private void BuildContentArea(GameObject parent)
    {
        // Viewport (clips content)
        var vpGo = MakeUIObj("Viewport", parent);
        _viewportRect = vpGo.GetComponent<RectTransform>();
        _viewportRect.anchorMin = new Vector2(0, 0);
        _viewportRect.anchorMax = new Vector2(1, 1);
        _viewportRect.offsetMin = new Vector2(2, 2);
        _viewportRect.offsetMax = new Vector2(-2, -CONTENT_TOP);
        var vpImg = vpGo.AddComponent<Image>();
        vpImg.color = new Color(0, 0, 0, 0.01f);
        vpGo.AddComponent<RectMask2D>();

        // Content container (grows with items)
        _contentGo = MakeUIObj("Content", vpGo);
        _contentRect = _contentGo.GetComponent<RectTransform>();
        _contentRect.anchorMin = new Vector2(0, 1);
        _contentRect.anchorMax = new Vector2(1, 1);
        _contentRect.pivot = new Vector2(0.5f, 1);
        _contentRect.anchoredPosition = Vector2.zero;
        // Height set dynamically when content is built
    }

    // ═══════════════════════════════════════
    //  CONTENT BUILDING
    // ═══════════════════════════════════════

    public void RebuildContent()
    {
        // Destroy old rows
        foreach (var r in _rows)
            if (r.Rect != null) UnityEngine.Object.Destroy(r.Rect.gameObject);
        _rows.Clear();

        if (_contentGo == null) return;

        // Build items
        var items = new List<ContentItem>();
        HackMenu.BuildTabItems(_currentTab, items);

        float y = -ROW_PAD;
        foreach (var item in items)
        {
            var go = MakeUIObj("Row", _contentGo);
            var rect = go.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0, 1);
            rect.anchorMax = new Vector2(1, 1);
            rect.pivot = new Vector2(0.5f, 1);
            rect.offsetMin = new Vector2(ROW_PAD, 0);
            rect.offsetMax = new Vector2(-ROW_PAD, 0);
            rect.anchoredPosition = new Vector2(0, y);
            rect.sizeDelta = new Vector2(0, ROW_H);

            if (item.IsHeader)
            {
                // Header row - no background, just centered text
                var txt = MakeText(go, "", 11, AccentRed, TMPro.TextAlignmentOptions.Center);
                FillParent(txt.GetComponent<RectTransform>());
                _rows.Add(new UIBtn
                {
                    Rect = rect, Label = txt,
                    GetText = () => $"── {item.Label} ──",
                    DefaultColor = Color.clear
                });
            }
            else
            {
                // Interactive row
                var bg = go.AddComponent<Image>();
                bg.color = item.IsAction ? RowAction : RowDef;

                var txt = MakeText(go, "", 12, TextWhite, TMPro.TextAlignmentOptions.Left);
                var txtRect = txt.GetComponent<RectTransform>();
                txtRect.anchorMin = new Vector2(0, 0);
                txtRect.anchorMax = new Vector2(1, 1);
                txtRect.offsetMin = new Vector2(8, 0);
                txtRect.offsetMax = new Vector2(-8, 0);

                var getText = item.GetText;
                var onClick = item.OnClick;

                _rows.Add(new UIBtn
                {
                    Rect = rect, Bg = bg, Label = txt,
                    OnClick = onClick, GetText = getText,
                    DefaultColor = item.IsAction ? RowAction : RowDef
                });
            }

            y -= ROW_H + ROW_GAP;
        }

        float totalH = Mathf.Abs(y) + ROW_PAD;
        _contentRect.sizeDelta = new Vector2(0, totalH);
        float viewH = WIN_H - CONTENT_TOP - 4f;
        _maxScrollY = Mathf.Max(0, totalH - viewH);
        _scrollY = Mathf.Clamp(_scrollY, 0, _maxScrollY);
        _contentRect.anchoredPosition = new Vector2(0, _scrollY);
    }

    // ═══════════════════════════════════════
    //  INPUT HANDLING
    // ═══════════════════════════════════════

    private void HandleDrag(Vector2 mouse, bool clicked, bool held)
    {
        if (clicked && HitTest(_titleBarRect, mouse))
        {
            _isDragging = true;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                _canvasRect, mouse, null, out var local);
            _dragOffset = (Vector2)_windowRect.localPosition - local;
        }

        if (_isDragging && held)
        {
            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                _canvasRect, mouse, null, out var local);
            _windowRect.localPosition = (Vector3)(local + _dragOffset);
        }

        if (!held) _isDragging = false;
    }

    private void HandleScroll(Vector2 mouse)
    {
        if (!HitTest(_viewportRect, mouse)) return;
        float scroll = UnityEngine.Input.mouseScrollDelta.y;
        if (Mathf.Abs(scroll) < 0.01f) return;
        _scrollY = Mathf.Clamp(_scrollY - scroll * 30f, 0, _maxScrollY);
        if (_contentRect != null)
            _contentRect.anchoredPosition = new Vector2(0, _scrollY);
    }

    // ═══════════════════════════════════════
    //  HELPERS
    // ═══════════════════════════════════════

    private static bool HitTest(RectTransform rect, Vector2 screenPoint)
    {
        if (rect == null) return false;
        return RectTransformUtility.RectangleContainsScreenPoint(rect, screenPoint, null);
    }

    private static void UpdateHover(ref UIBtn btn, bool hover)
    {
        if (btn.Bg == null) return;
        if (hover && !btn.IsHovered) btn.Bg.color = RowHover;
        else if (!hover && btn.IsHovered) btn.Bg.color = btn.DefaultColor;
        btn.IsHovered = hover;
    }

    private static GameObject MakeUIObj(string name, GameObject parent)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent.transform, false);
        if (go.GetComponent<RectTransform>() == null)
            go.AddComponent<RectTransform>();
        return go;
    }

    private static TMPro.TextMeshProUGUI MakeText(GameObject parent, string text, float size, Color color, TMPro.TextAlignmentOptions align)
    {
        var go = MakeUIObj("Text", parent);
        var tmp = go.AddComponent<TMPro.TextMeshProUGUI>();
        tmp.text = text;
        tmp.fontSize = size;
        tmp.color = color;
        tmp.alignment = align;
        tmp.overflowMode = TMPro.TextOverflowModes.Ellipsis;
        tmp.richText = true;
        var font = GetFont();
        if (font != null) tmp.font = font;
        return tmp;
    }

    private static void AnchorTop(RectTransform r, float y, float w, float h)
    {
        r.anchorMin = new Vector2(0, 1);
        r.anchorMax = new Vector2(1, 1);
        r.pivot = new Vector2(0.5f, 1);
        r.anchoredPosition = new Vector2(0, -y);
        r.sizeDelta = new Vector2(0, h);
    }

    private static void FillParent(RectTransform r)
    {
        r.anchorMin = Vector2.zero;
        r.anchorMax = Vector2.one;
        r.offsetMin = Vector2.zero;
        r.offsetMax = Vector2.zero;
    }

    private static TMPro.TMP_FontAsset GetFont()
    {
        if (_font != null) return _font;
        try
        {
            var existing = UnityEngine.Object.FindObjectOfType<TMPro.TextMeshProUGUI>();
            if (existing != null) _font = existing.font;
        }
        catch { }
        if (_font == null)
        {
            try
            {
                var existing3d = UnityEngine.Object.FindObjectOfType<TMPro.TextMeshPro>();
                if (existing3d != null) _font = existing3d.font;
            }
            catch { }
        }
        return _font;
    }

    // ═══════════════════════════════════════
    //  CONTENT ITEM (shared with HackMenu)
    // ═══════════════════════════════════════

    public struct ContentItem
    {
        public string Label;
        public bool IsHeader;
        public bool IsAction;
        public Action OnClick;
        public Func<string> GetText;
    }
}

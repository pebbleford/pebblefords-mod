using System;
using System.Collections.Generic;
using UnityEngine;
using HarmonyLib;

namespace CustomMod.Features;

public class HackMenu : MonoBehaviour
{
    public HackMenu(IntPtr ptr) : base(ptr) { }

    // ── Menu State ──
    public static bool ShowMenu = false;

    // ══════════════════════════════════════
    //  HACK TOGGLES
    // ══════════════════════════════════════

    // Vision
    public static bool EspEnabled, SeeRolesEnabled, FullVisionEnabled, FreeCamEnabled;
    public static bool ZoomOutHackEnabled, SeeGhostsEnabled, AlwaysShowNamesEnabled;
    public static bool ShowDeadBodiesEnabled, ShowVentsEnabled, AntiInvisEnabled;
    public static float ZoomOutHackLevel = 6f;

    // Movement
    public static bool NoClipEnabled, SpeedHackEnabled, MouseTeleportEnabled;
    public static bool FreezePositionEnabled, FlipEnabled;
    public static float SpeedHackMultiplier = 3f;

    // Combat
    public static bool ZeroCooldownEnabled, KillAuraEnabled, AutoReportEnabled;
    public static bool VentAsCrewmateEnabled, InfiniteKillRangeEnabled;
    public static bool AntiKillEnabled, AutoKillOnSightEnabled;
    public static float KillAuraRange = 2f;

    // Troll
    public static bool SpamChatEnabled, ForceColorEnabled;
    public static int ForceColorId = 0;

    // Player
    public static bool GodModeEnabled, NoTasksEnabled, InfiniteEmergencyEnabled;

    // Cosmetics
    public static bool UnlockAllCosmeticsEnabled;

    // Doors
    public static bool PinDoorsEnabled;
    public static HashSet<SystemTypes> PinnedRooms = new HashSet<SystemTypes>();

    // Meeting
    public static bool SeeRolesInMeetingEnabled;

    // ── Internal State ──
    private Vector3 _freeCamPos;
    private bool _freeCamInit;
    private float _killAuraTimer, _spamTimer, _autoKillTimer, _pinDoorTimer;
    private int _spamIndex;
    private Vector3 _frozenPosition;
    private bool _frozenPosSet;
    private float _defaultZoom = 3f;
    private bool _defaultZoomCaptured;
    private float _defaultSpeed = 2.5f;
    private bool _defaultSpeedCaptured;
    private static int _hatIdx, _skinIdx, _visorIdx, _petIdx;

    private static readonly string[] SpamMessages = {
        "Pebbleford's Mod!", "sussy baka", "trust me bro", "i saw them vent",
        "it wasnt me", "voted", "where body", "emergency!!!", "skip skip skip",
        "im innocent", "who called", "why", "bruh", "they self reported",
        "its red", "its blue", "cap", "i was in electrical", "no way",
        "Pebbleford on top!", "gg ez", "sussy sussy", "everyone sus ngl"
    };
    private static readonly string[] ColorNames = {
        "Red", "Blue", "Green", "Pink", "Orange", "Yellow",
        "Black", "White", "Purple", "Brown", "Cyan", "Lime",
        "Maroon", "Rose", "Banana", "Gray", "Tan", "Coral"
    };

    // ── UI ──
    private HackMenuUI _ui;

    // ══════════════════════════════════════
    //  UPDATE
    // ══════════════════════════════════════

    void Update()
    {
        try
        {
            // Capture default zoom once (only when in-game so we get the real value)
            if (!_defaultZoomCaptured && Camera.main != null && ShipStatus.Instance != null)
            {
                _defaultZoom = Camera.main.orthographicSize;
                _defaultZoomCaptured = true;
            }

            if (UnityEngine.Input.GetKeyDown(KeyCode.Insert) || UnityEngine.Input.GetKeyDown(KeyCode.Delete))
            {
                ShowMenu = !ShowMenu;
                _ui?.SetVisible(ShowMenu);
            }

            // Right-click teleport
            if (MouseTeleportEnabled && UnityEngine.Input.GetMouseButtonDown(1) && !ShowMenu)
            {
                try
                {
                    var cam = Camera.main;
                    if (cam != null && PlayerControl.LocalPlayer != null)
                    {
                        var world = cam.ScreenToWorldPoint(UnityEngine.Input.mousePosition);
                        var pos = new Vector2(world.x, world.y);
                        PlayerControl.LocalPlayer.NetTransform.RpcSnapTo(pos);
                    }
                }
                catch { }
            }

            ApplyHacks();

            if (ShowMenu)
            {
                if (_ui == null) _ui = new HackMenuUI();
                _ui.EnsureBuilt();
                _ui.HandleInput();
            }
        }
        catch { }
    }

    // ══════════════════════════════════════
    //  TAB CONTENT BUILDER (called by UI)
    // ══════════════════════════════════════

    public static void BuildTabItems(int tab, List<HackMenuUI.ContentItem> items)
    {
        Action<string, Func<bool>, Action> toggle = (label, get, act) =>
        {
            var g = get; var a = act;
            items.Add(new HackMenuUI.ContentItem
            {
                Label = label, IsHeader = false, IsAction = false,
                OnClick = a,
                GetText = () => (g() ? "<color=#1adb1a>[ON]</color>" : "<color=#cc3333>[OFF]</color>") + "  " + label
            });
        };

        Action<string, Action> action = (label, act) =>
        {
            var a = act;
            items.Add(new HackMenuUI.ContentItem
            {
                Label = label, IsHeader = false, IsAction = true,
                OnClick = a,
                GetText = () => "<color=#ff6b6b>►</color>  " + label
            });
        };

        Action<string> header = (label) =>
        {
            items.Add(new HackMenuUI.ContentItem { Label = label, IsHeader = true });
        };

        Action<string, Func<string>, Action> info = (label, getText, act) =>
        {
            var gt = getText; var a = act;
            items.Add(new HackMenuUI.ContentItem
            {
                Label = label, IsHeader = false, IsAction = false,
                OnClick = a,
                GetText = () => "<color=#6688ff>◆</color>  " + gt()
            });
        };

        switch (tab)
        {
            case 0: // Vision
                toggle("ESP + Distance + Cooldown", () => EspEnabled, () => EspEnabled = !EspEnabled);
                toggle("See Roles (Imp = Red)", () => SeeRolesEnabled, () => SeeRolesEnabled = !SeeRolesEnabled);
                toggle("See Roles in Meetings", () => SeeRolesInMeetingEnabled, () => SeeRolesInMeetingEnabled = !SeeRolesInMeetingEnabled);
                toggle("Full Brightness", () => FullVisionEnabled, () => FullVisionEnabled = !FullVisionEnabled);
                toggle("Free Camera (WASD/Arrows)", () => FreeCamEnabled, () => FreeCamEnabled = !FreeCamEnabled);
                toggle("Zoom Out", () => ZoomOutHackEnabled, () => ZoomOutHackEnabled = !ZoomOutHackEnabled);
                info($"Zoom Level: {ZoomOutHackLevel:F0}", () => $"Zoom: {ZoomOutHackLevel:F0}x  [click to cycle]",
                    () => ZoomOutHackLevel = ZoomOutHackLevel >= 12f ? 3f : ZoomOutHackLevel + 1f);
                toggle("See Ghosts", () => SeeGhostsEnabled, () => SeeGhostsEnabled = !SeeGhostsEnabled);
                toggle("Always Show Names", () => AlwaysShowNamesEnabled, () => AlwaysShowNamesEnabled = !AlwaysShowNamesEnabled);
                toggle("Dead Body ESP", () => ShowDeadBodiesEnabled, () => ShowDeadBodiesEnabled = !ShowDeadBodiesEnabled);
                toggle("Highlight Vents", () => ShowVentsEnabled, () => ShowVentsEnabled = !ShowVentsEnabled);
                toggle("Anti-Invisible (Phantoms)", () => AntiInvisEnabled, () => AntiInvisEnabled = !AntiInvisEnabled);
                break;

            case 1: // Move
                toggle("No Clip", () => NoClipEnabled, () => NoClipEnabled = !NoClipEnabled);
                toggle("Speed Hack", () => SpeedHackEnabled, () => SpeedHackEnabled = !SpeedHackEnabled);
                info($"Speed: {SpeedHackMultiplier:F1}x", () => $"Speed: {SpeedHackMultiplier:F1}x  [click to cycle]",
                    () => SpeedHackMultiplier = SpeedHackMultiplier >= 10f ? 1f : SpeedHackMultiplier + 0.5f);
                toggle("Right-Click Teleport", () => MouseTeleportEnabled, () => MouseTeleportEnabled = !MouseTeleportEnabled);
                toggle("Freeze Position", () => FreezePositionEnabled, () => {
                    FreezePositionEnabled = !FreezePositionEnabled;
                    if (FreezePositionEnabled && PlayerControl.LocalPlayer != null)
                    {
                        var inst = UnityEngine.Object.FindObjectOfType<HackMenu>();
                        if (inst != null) { inst._frozenPosition = PlayerControl.LocalPlayer.transform.position; inst._frozenPosSet = true; }
                    }
                });
                toggle("Flip Character", () => FlipEnabled, () => FlipEnabled = !FlipEnabled);
                action("Teleport to Nearest", () => TeleportToNearest());
                action("Teleport to Random Vent", () => TeleportToRandomVent());
                break;

            case 2: // Combat
                toggle("Zero Kill Cooldown", () => ZeroCooldownEnabled, () => ZeroCooldownEnabled = !ZeroCooldownEnabled);
                toggle("Kill Aura (Auto-Kill)", () => KillAuraEnabled, () => KillAuraEnabled = !KillAuraEnabled);
                info($"Kill Range: {KillAuraRange:F1}", () => $"Kill Range: {KillAuraRange:F1}  [click +]",
                    () => KillAuraRange = KillAuraRange >= 5f ? 0.5f : KillAuraRange + 0.5f);
                toggle("Infinite Kill Range", () => InfiniteKillRangeEnabled, () => InfiniteKillRangeEnabled = !InfiniteKillRangeEnabled);
                toggle("Auto Report Bodies", () => AutoReportEnabled, () => AutoReportEnabled = !AutoReportEnabled);
                toggle("Vent as Crewmate", () => VentAsCrewmateEnabled, () => VentAsCrewmateEnabled = !VentAsCrewmateEnabled);
                toggle("Anti-Kill (Can't Die)", () => AntiKillEnabled, () => AntiKillEnabled = !AntiKillEnabled);
                toggle("Auto Kill Imps On Sight", () => AutoKillOnSightEnabled, () => AutoKillOnSightEnabled = !AutoKillOnSightEnabled);
                action("Kill Nearest", () => KillNearest());
                action("Kill ALL", () => KillAllPlayers());
                action("Call Emergency Meeting", () => CallMeeting());
                break;

            case 3: // Troll
                header("Sabotage");
                action("Sabotage Lights", () => SabotageLights());
                action("Sabotage Reactor", () => SabotageReactor());
                action("Sabotage O2", () => SabotageO2());
                action("Sabotage Comms", () => SabotageComms());
                action("Fix All Sabotages", () => FixSabotages());
                header("Other");
                toggle("Chat Spam", () => SpamChatEnabled, () => SpamChatEnabled = !SpamChatEnabled);
                action("Shapeshift to Nearest", () => ShapeshiftToNearest());
                action("Vanish (Phantom)", () => DoVanish());
                action("Scanner Animation", () => SetScanner());
                toggle("Force Color", () => ForceColorEnabled, () => { ForceColorEnabled = !ForceColorEnabled; if (ForceColorEnabled) ApplyForceColor(); });
                info($"Color: {GetColorName(ForceColorId)}", () => $"Color: {GetColorName(ForceColorId)}  [click next]",
                    () => { ForceColorId = (ForceColorId + 1) % 18; if (ForceColorEnabled) ApplyForceColor(); });
                break;

            case 9: // Doors
                toggle("Pin ALL Doors (Keep Closed)", () => PinDoorsEnabled, () => PinDoorsEnabled = !PinDoorsEnabled);
                action("Close ALL Doors", () => CloseAllDoors());
                action("Open ALL Doors", () => OpenAllDoors());
                header("Pin By Room (Keep Closed)");
                foreach (var kv in DoorRooms)
                {
                    var r = kv.Key;
                    string roomName = kv.Value;
                    toggle($"Pin {roomName}", () => PinnedRooms.Contains(r), () => { if (PinnedRooms.Contains(r)) PinnedRooms.Remove(r); else { PinnedRooms.Add(r); try { ShipStatus.Instance?.RpcCloseDoorsOfType(r); } catch { } } });
                }
                header("Close By Room");
                foreach (var kv in DoorRooms)
                {
                    var r = kv.Key;
                    string roomName = kv.Value;
                    action($"Close {roomName}", () => { try { ShipStatus.Instance?.RpcCloseDoorsOfType(r); } catch { } });
                }
                header("Open By Room");
                foreach (var kv in DoorRooms)
                {
                    var r = kv.Key;
                    string roomName = kv.Value;
                    action($"Open {roomName}", () => OpenDoorsForRoom(r));
                }
                break;

            case 4: // Game
                action("Complete All Tasks", () => CompleteAllTasks());
                action("Revive Self", () => ReviveSelf());
                toggle("God Mode", () => GodModeEnabled, () => GodModeEnabled = !GodModeEnabled);
                toggle("No Tasks (Auto)", () => NoTasksEnabled, () => NoTasksEnabled = !NoTasksEnabled);
                toggle("Infinite Emergencies", () => InfiniteEmergencyEnabled, () => InfiniteEmergencyEnabled = !InfiniteEmergencyEnabled);
                action("Force End Game", () => ForceEndGame());
                header("Players");
                try
                {
                    if (PlayerControl.AllPlayerControls != null)
                    {
                        foreach (var p in PlayerControl.AllPlayerControls)
                        {
                            if (p == null || p.Data == null) continue;
                            string pn = p.Data.PlayerName ?? "???";
                            string st = p.Data.IsDead ? "<color=#666>[DEAD]</color>" : "<color=#0f0>[ALIVE]</color>";
                            string rl = p.Data.Role != null && p.Data.Role.IsImpostor ? " <color=#f00>[IMP]</color>" : "";
                            var pRef = p;
                            string display = $"{pn} {st}{rl}";
                            items.Add(new HackMenuUI.ContentItem { Label = pn, IsAction = true, OnClick = () => TeleportToPlayer(pRef), GetText = () => display });
                        }
                    }
                }
                catch { }
                break;

            case 5: // Player
                header("Roles Config");
                toggle("Sheriff", () => CustomModPlugin.EnableSheriff.Value, () => CustomModPlugin.EnableSheriff.Value = !CustomModPlugin.EnableSheriff.Value);
                toggle("Jester", () => CustomModPlugin.EnableJester.Value, () => CustomModPlugin.EnableJester.Value = !CustomModPlugin.EnableJester.Value);
                toggle("Mayor", () => CustomModPlugin.EnableMayor.Value, () => CustomModPlugin.EnableMayor.Value = !CustomModPlugin.EnableMayor.Value);
                toggle("Seer", () => CustomModPlugin.EnableSeer.Value, () => CustomModPlugin.EnableSeer.Value = !CustomModPlugin.EnableSeer.Value);
                header("Features");
                toggle("Speed Boost", () => CustomModPlugin.EnableSpeedBoost.Value, () => CustomModPlugin.EnableSpeedBoost.Value = !CustomModPlugin.EnableSpeedBoost.Value);
                toggle("Zoom Out", () => CustomModPlugin.EnableZoomOut.Value, () => CustomModPlugin.EnableZoomOut.Value = !CustomModPlugin.EnableZoomOut.Value);
                toggle("Always Show Names", () => CustomModPlugin.AlwaysShowNames.Value, () => CustomModPlugin.AlwaysShowNames.Value = !CustomModPlugin.AlwaysShowNames.Value);
                toggle("Chaos Mode", () => CustomModPlugin.EnableChaosMode.Value, () => CustomModPlugin.EnableChaosMode.Value = !CustomModPlugin.EnableChaosMode.Value);
                toggle("Game Info HUD", () => CustomModPlugin.EnableGameInfo.Value, () => CustomModPlugin.EnableGameInfo.Value = !CustomModPlugin.EnableGameInfo.Value);
                header("Identity");
                action("Set Name: 'Pebbleford'", () => SetName("Pebbleford"));
                action("Set Name: '???'", () => SetName("???"));
                action("Set Name: (Blank)", () => SetName(" "));
                action("Random Color", () => RandomizeColor());
                break;

            case 6: // Teleport
                header("Skeld Locations");
                action("Cafeteria", () => TeleportToPos(new Vector2(-1f, 2f)));
                action("Admin", () => TeleportToPos(new Vector2(2.5f, -7.5f)));
                action("Navigation", () => TeleportToPos(new Vector2(16.3f, -4.8f)));
                action("Weapons", () => TeleportToPos(new Vector2(8.7f, 2.6f)));
                action("Shields", () => TeleportToPos(new Vector2(9.2f, -12.3f)));
                action("O2", () => TeleportToPos(new Vector2(6.3f, -3.5f)));
                action("Electrical", () => TeleportToPos(new Vector2(-7.5f, -8.6f)));
                action("Storage", () => TeleportToPos(new Vector2(-0.3f, -15.5f)));
                action("Reactor", () => TeleportToPos(new Vector2(-20.7f, -5.3f)));
                action("MedBay", () => TeleportToPos(new Vector2(-9f, -4f)));
                action("Security", () => TeleportToPos(new Vector2(-13.3f, -5.5f)));
                action("Communications", () => TeleportToPos(new Vector2(3.8f, -15.3f)));
                action("Lower Engine", () => TeleportToPos(new Vector2(-17f, -13.3f)));
                action("Upper Engine", () => TeleportToPos(new Vector2(-17f, 2.4f)));
                header("Players");
                action("Nearest Player", () => TeleportToNearest());
                action("Random Vent", () => TeleportToRandomVent());
                try
                {
                    if (PlayerControl.AllPlayerControls != null)
                        foreach (var p in PlayerControl.AllPlayerControls)
                        {
                            if (p == null || p.Data == null || p == PlayerControl.LocalPlayer || p.Data.IsDead || p.Data.Disconnected) continue;
                            var pRef = p; string pn = p.Data.PlayerName ?? "???";
                            action(pn, () => TeleportToPlayer(pRef));
                        }
                }
                catch { }
                break;

            case 7: // Chat
                toggle("Chat Spam", () => SpamChatEnabled, () => SpamChatEnabled = !SpamChatEnabled);
                header("Quick Messages");
                action("'It's not me!'", () => SendChat("It's not me!"));
                action("'I saw them vent!'", () => SendChat("I saw them vent!"));
                action("'Trust me bro'", () => SendChat("Trust me bro"));
                action("'Skip please'", () => SendChat("Skip please"));
                action("'Self report!!'", () => SendChat("Self report!!"));
                action("'Where?'", () => SendChat("Where?"));
                action("'I was doing tasks'", () => SendChat("I was doing tasks"));
                action("Vote Random Player", () => SendVoteRandom());
                action("'I'm Impostor jk'", () => SendChat("I'm the Impostor! ...jk"));
                action("ඞ SUS ඞ", () => SendChat("ඞ ඞ ඞ SUS ඞ ඞ ඞ"));
                action("Pebbleford's Mod!", () => SendChat("Pebbleford's Mod is the best!"));
                break;

            case 8: // Cosmetics
                toggle("Unlock ALL Cosmetics", () => UnlockAllCosmeticsEnabled, () => UnlockAllCosmeticsEnabled = !UnlockAllCosmeticsEnabled);
                header("Hats");
                action("Next Hat →", () => CycleHat(1));
                action("← Previous Hat", () => CycleHat(-1));
                action("Random Hat", () => RandomHat());
                action("Remove Hat", () => SetHat("hat_EmptyHat"));
                header("Skins");
                action("Next Skin →", () => CycleSkin(1));
                action("← Previous Skin", () => CycleSkin(-1));
                action("Random Skin", () => RandomSkin());
                action("Remove Skin", () => SetSkinId("skin_None"));
                header("Visors");
                action("Next Visor →", () => CycleVisor(1));
                action("← Previous Visor", () => CycleVisor(-1));
                action("Random Visor", () => RandomVisor());
                action("Remove Visor", () => SetVisorId("visor_EmptyVisor"));
                header("Pets");
                action("Next Pet →", () => CyclePet(1));
                action("← Previous Pet", () => CyclePet(-1));
                action("Random Pet", () => RandomPet());
                action("Remove Pet", () => SetPetId("pet_EmptyPet"));
                header("Quick Sets");
                action("Randomize EVERYTHING", () => { RandomHat(); RandomSkin(); RandomVisor(); RandomPet(); RandomizeColor(); });
                action("Remove ALL Cosmetics", () => { SetHat("hat_EmptyHat"); SetSkinId("skin_None"); SetVisorId("visor_EmptyVisor"); SetPetId("pet_EmptyPet"); });
                break;
        }
    }

    // ══════════════════════════════════════
    //  HACK LOGIC (every frame)
    // ══════════════════════════════════════

    private void ApplyHacks()
    {
        if (PlayerControl.LocalPlayer == null) return;
        var local = PlayerControl.LocalPlayer;
        if (local.Data == null) return;

        try { if (local.Collider != null) local.Collider.enabled = !NoClipEnabled; } catch { }
        try
        {
            if (local.MyPhysics != null)
            {
                if (!_defaultSpeedCaptured) { _defaultSpeed = local.MyPhysics.Speed; _defaultSpeedCaptured = true; }
                if (SpeedHackEnabled) local.MyPhysics.Speed = SpeedHackMultiplier;
                else if (_defaultSpeedCaptured && local.MyPhysics.Speed > _defaultSpeed + 0.1f) local.MyPhysics.Speed = _defaultSpeed;
            }
        }
        catch { }

        // Freeze
        try { if (FreezePositionEnabled && _frozenPosSet) { local.NetTransform.RpcSnapTo((Vector2)_frozenPosition); } } catch { }

        // Flip
        try { if (FlipEnabled && local.MyPhysics != null) local.MyPhysics.FlipX = !local.MyPhysics.FlipX; } catch { }

        // Free Cam - disable FollowerCamera so it doesn't override position
        try
        {
            if (FreeCamEnabled)
            {
                var cam = Camera.main;
                if (cam != null)
                {
                    var follower = cam.GetComponent<FollowerCamera>();
                    if (follower != null) follower.enabled = false;
                    if (!_freeCamInit) { _freeCamPos = cam.transform.position; _freeCamInit = true; }
                    float s = 8f * Time.deltaTime;
                    if (UnityEngine.Input.GetKey(KeyCode.UpArrow)) _freeCamPos.y += s;
                    if (UnityEngine.Input.GetKey(KeyCode.DownArrow)) _freeCamPos.y -= s;
                    if (UnityEngine.Input.GetKey(KeyCode.LeftArrow)) _freeCamPos.x -= s;
                    if (UnityEngine.Input.GetKey(KeyCode.RightArrow)) _freeCamPos.x += s;
                    if (UnityEngine.Input.GetKey(KeyCode.W)) _freeCamPos.y += s;
                    if (UnityEngine.Input.GetKey(KeyCode.S)) _freeCamPos.y -= s;
                    if (UnityEngine.Input.GetKey(KeyCode.A)) _freeCamPos.x -= s;
                    if (UnityEngine.Input.GetKey(KeyCode.D)) _freeCamPos.x += s;
                    cam.transform.position = new Vector3(_freeCamPos.x, _freeCamPos.y, cam.transform.position.z);
                }
            }
            else if (_freeCamInit)
            {
                _freeCamInit = false;
                var cam = Camera.main;
                if (cam != null)
                {
                    var follower = cam.GetComponent<FollowerCamera>();
                    if (follower != null) follower.enabled = true;
                }
            }
        }
        catch { }

        // Zoom - FIXED: resets when disabled
        try
        {
            if (ZoomOutHackEnabled && Camera.main != null)
                Camera.main.orthographicSize = ZoomOutHackLevel;
            else if (!ZoomOutHackEnabled && Camera.main != null && Camera.main.orthographicSize > _defaultZoom + 0.1f)
                Camera.main.orthographicSize = _defaultZoom;
        }
        catch { }

        // Vent as Crewmate - force vent button visible
        if (VentAsCrewmateEnabled)
        {
            try
            {
                var hud = HudManager.Instance;
                if (hud != null && hud.ImpostorVentButton != null)
                {
                    var ventBtn = hud.ImpostorVentButton.gameObject;
                    if (ventBtn != null && !ventBtn.active) ventBtn.SetActive(true);
                    hud.ImpostorVentButton.Show();
                }
            }
            catch { }
            // Also set CanVent on the role so the physics allow entering
            try { if (local.Data?.Role != null) local.Data.Role.CanVent = true; } catch { }
        }

        // Zero Kill Cooldown - force every frame + reset button
        if (ZeroCooldownEnabled)
        {
            try { local.killTimer = 0f; } catch { }
            try
            {
                var kb = HudManager.Instance?.KillButton;
                if (kb != null)
                {
                    kb.SetCoolDown(0f, 0.5f);
                    kb.isCoolingDown = false;
                }
            }
            catch { }
        }

        // Infinite Kill Range
        try { if (InfiniteKillRangeEnabled) local.MaxReportDistance = 9999f; } catch { }

        // Infinite Emergency
        try { if (InfiniteEmergencyEnabled) local.RemainingEmergencies = 99; } catch { }

        // God Mode
        try { if ((GodModeEnabled || AntiKillEnabled) && local.Data.IsDead) try { local.Revive(); } catch { } } catch { }

        // No Tasks (server-sided)
        if (NoTasksEnabled) try { for (int i = 0; i < local.myTasks.Count; i++) { var t = local.myTasks[i]; if (t != null && !t.IsComplete) try { local.RpcCompleteTask(t.Id); } catch { } } } catch { }

        // ESP / Roles / Names
        if (EspEnabled || SeeRolesEnabled || AlwaysShowNamesEnabled)
        {
            try
            {
                foreach (var p in PlayerControl.AllPlayerControls)
                {
                    if (p == null) continue;
                    try
                    {
                        if (p.cosmetics?.nameText == null) continue;
                        var nt = p.cosmetics.nameText;
                        nt.gameObject.SetActive(true);
                        if (p.Data?.Role != null && (SeeRolesEnabled || EspEnabled))
                        {
                            nt.color = p.Data.IsDead ? new Color(0.5f, 0.5f, 0.5f, 0.7f) :
                                       p.Data.Role.IsImpostor ? Color.red : Color.green;
                        }
                        if (EspEnabled)
                        {
                            float d = p == local ? 0f : Vector2.Distance(local.GetTruePosition(), p.GetTruePosition());
                            string imp = p.Data.Role != null && p.Data.Role.IsImpostor ? " [IMP]" : "";
                            string cd = "";
                            try { if (p.Data.Role != null && p.Data.Role.IsImpostor) { float t = p.killTimer; cd = $" CD:{t:F1}s"; } } catch { }
                            if (p == local)
                                nt.text = (p.Data.PlayerName ?? "") + imp + cd;
                            else
                                nt.text = (p.Data.PlayerName ?? "") + imp + cd + $" [{d:F1}m]";
                        }
                    }
                    catch { }
                }
            }
            catch { }
        }

        // See Ghosts
        if (SeeGhostsEnabled) try { foreach (var p in PlayerControl.AllPlayerControls) if (p?.Data != null && p.Data.IsDead) try { p.Visible = true; p.cosmetics?.nameText?.gameObject.SetActive(true); } catch { } } catch { }

        // Anti-Invisible
        if (AntiInvisEnabled) try { foreach (var p in PlayerControl.AllPlayerControls) { if (p == null || p == local) continue; try { p.Visible = true; p.cosmetics?.SetPhantomRoleAlpha(1f); } catch { } } } catch { }

        // Dead Body ESP
        if (ShowDeadBodiesEnabled) try { foreach (var b in UnityEngine.Object.FindObjectsOfType<DeadBody>()) { if (b == null) continue; try { var sr = b.GetComponentInChildren<SpriteRenderer>(); if (sr != null) sr.color = new Color(1f, 0.3f, 0.3f, 1f); } catch { } } } catch { }

        // Vent ESP
        if (ShowVentsEnabled) try { foreach (var v in UnityEngine.Object.FindObjectsOfType<Vent>()) { if (v == null) continue; try { var sr = v.GetComponent<SpriteRenderer>(); if (sr != null) sr.color = new Color(0.3f, 1f, 0.3f, 0.9f); } catch { } } } catch { }

        // Kill Aura
        if (KillAuraEnabled && ShipStatus.Instance != null)
        {
            _killAuraTimer -= Time.deltaTime;
            if (_killAuraTimer <= 0f)
            {
                _killAuraTimer = 0.3f;
                try { foreach (var p in PlayerControl.AllPlayerControls) { if (p == null || p == local || p.Data == null || p.Data.IsDead) continue; if (Vector2.Distance(local.GetTruePosition(), p.GetTruePosition()) <= KillAuraRange) { try { local.RpcMurderPlayer(p, true); } catch { } break; } } } catch { }
            }
        }

        // Auto Kill Imps
        if (AutoKillOnSightEnabled && ShipStatus.Instance != null)
        {
            _autoKillTimer -= Time.deltaTime;
            if (_autoKillTimer <= 0f)
            {
                _autoKillTimer = 0.5f;
                try { foreach (var p in PlayerControl.AllPlayerControls) { if (p == null || p == local || p.Data == null || p.Data.IsDead) continue; if (p.Data.Role?.IsImpostor == true && Vector2.Distance(local.GetTruePosition(), p.GetTruePosition()) < 3f) { try { local.RpcMurderPlayer(p, true); } catch { } break; } } } catch { }
            }
        }

        // Auto Report
        if (AutoReportEnabled && ShipStatus.Instance != null)
            try { foreach (var b in UnityEngine.Object.FindObjectsOfType<DeadBody>()) { if (b == null) continue; if (Vector2.Distance(local.GetTruePosition(), (Vector2)b.transform.position) < local.MaxReportDistance) { try { local.CmdReportDeadBody(GameData.Instance.GetPlayerById(b.ParentId)); } catch { } break; } } } catch { }

        // Pin Doors - re-close pinned doors every 2 seconds
        if ((PinDoorsEnabled || PinnedRooms.Count > 0) && ShipStatus.Instance != null)
        {
            _pinDoorTimer -= Time.deltaTime;
            if (_pinDoorTimer <= 0f)
            {
                _pinDoorTimer = 2f;
                if (PinDoorsEnabled)
                    try { foreach (var kv in DoorRooms) try { ShipStatus.Instance.RpcCloseDoorsOfType(kv.Key); } catch { } } catch { }
                else
                    try { foreach (var room in PinnedRooms) try { ShipStatus.Instance.RpcCloseDoorsOfType(room); } catch { } } catch { }
            }
        }

        // See Roles in Meeting
        if (SeeRolesInMeetingEnabled)
        {
            try
            {
                var meeting = MeetingHud.Instance;
                if (meeting != null && meeting.playerStates != null)
                {
                    foreach (var pva in meeting.playerStates)
                    {
                        if (pva == null || pva.NameText == null) continue;
                        try
                        {
                            var playerInfo = GameData.Instance?.GetPlayerById(pva.TargetPlayerId);
                            if (playerInfo == null || playerInfo.Role == null) continue;
                            string roleName = playerInfo.Role.IsImpostor ? " <color=#ff0000>[IMP]</color>" : " <color=#00ff00>[CREW]</color>";
                            string name = playerInfo.PlayerName ?? "???";
                            pva.NameText.text = name + roleName;
                        }
                        catch { }
                    }
                }
            }
            catch { }
        }

        // Chat Spam
        if (SpamChatEnabled)
        {
            _spamTimer -= Time.deltaTime;
            if (_spamTimer <= 0f)
            {
                _spamTimer = 1.5f;
                SendChat(SpamMessages[_spamIndex++ % SpamMessages.Length]);
            }
        }
    }

    // ══════════════════════════════════════
    //  ACTIONS
    // ══════════════════════════════════════

    private static void KillNearest() { try { var n = GetNearest(); if (n != null) PlayerControl.LocalPlayer.RpcMurderPlayer(n, true); } catch { } }
    private static void KillAllPlayers() { try { foreach (var p in PlayerControl.AllPlayerControls) if (p != null && p != PlayerControl.LocalPlayer && p.Data != null && !p.Data.IsDead) try { PlayerControl.LocalPlayer.RpcMurderPlayer(p, true); } catch { } } catch { } }
    private static void CallMeeting() { try { PlayerControl.LocalPlayer.CmdReportDeadBody(null); } catch { } }

    private static void TeleportToNearest() { try { var n = GetNearest(); if (n != null) TeleportToPlayer(n); } catch { } }
    private static void TeleportToPlayer(PlayerControl t) { try { if (t != null) PlayerControl.LocalPlayer.NetTransform.RpcSnapTo((Vector2)t.transform.position); } catch { } }
    private static void TeleportToPos(Vector2 p) { try { PlayerControl.LocalPlayer.NetTransform.RpcSnapTo(p); } catch { } }
    private static void TeleportToRandomVent() { try { var vents = UnityEngine.Object.FindObjectsOfType<Vent>(); if (vents.Length > 0) { var v = vents[UnityEngine.Random.Range(0, vents.Length)]; PlayerControl.LocalPlayer.NetTransform.RpcSnapTo((Vector2)v.transform.position); } } catch { } }

    private static void CompleteAllTasks()
    {
        try
        {
            var local = PlayerControl.LocalPlayer;
            for (int i = 0; i < local.myTasks.Count; i++)
            {
                var t = local.myTasks[i];
                if (t != null && !t.IsComplete)
                {
                    try { t.Complete(); } catch { }
                    try { local.RpcCompleteTask(t.Id); } catch { }
                }
            }
        }
        catch { }
    }
    private static void ReviveSelf() { try { PlayerControl.LocalPlayer.Revive(); } catch { } }
    private static void ShapeshiftToNearest() { try { var n = GetNearest(); if (n != null) PlayerControl.LocalPlayer.RpcShapeshift(n, true); } catch { } }
    private static void DoVanish() { try { PlayerControl.LocalPlayer.CmdCheckVanish(9999f); } catch { } }
    private static void SetScanner() { try { PlayerControl.LocalPlayer.RpcSetScanner(true); } catch { } }

    // Door rooms list (all maps)
    private static readonly KeyValuePair<SystemTypes, string>[] DoorRooms = {
        new(SystemTypes.Cafeteria, "Cafeteria"),
        new(SystemTypes.MedBay, "MedBay"),
        new(SystemTypes.Security, "Security"),
        new(SystemTypes.Electrical, "Electrical"),
        new(SystemTypes.Storage, "Storage"),
        new(SystemTypes.Reactor, "Reactor"),
        new(SystemTypes.UpperEngine, "Upper Engine"),
        new(SystemTypes.LowerEngine, "Lower Engine"),
        new(SystemTypes.LifeSupp, "O2"),
        new(SystemTypes.Nav, "Navigation"),
        new(SystemTypes.Comms, "Comms"),
        new(SystemTypes.Admin, "Admin"),
        new(SystemTypes.Weapons, "Weapons"),
        new(SystemTypes.Shields, "Shields"),
        new(SystemTypes.Decontamination, "Decontamination"),
        new(SystemTypes.Decontamination2, "Decontamination 2"),
        new(SystemTypes.Laboratory, "Laboratory"),
        new(SystemTypes.Launchpad, "Launchpad"),
        new(SystemTypes.Office, "Office"),
    };

    // Doors - uses RPC to sync to all players
    private static void CloseAllDoors()
    {
        try
        {
            if (ShipStatus.Instance == null) return;
            foreach (var kv in DoorRooms)
                try { ShipStatus.Instance.RpcCloseDoorsOfType(kv.Key); } catch { }
        }
        catch { }
    }

    private static void OpenAllDoors()
    {
        try
        {
            if (ShipStatus.Instance == null) return;
            // Open doors by repairing the door system for each door ID
            if (ShipStatus.Instance.AllDoors != null)
            {
                foreach (var door in ShipStatus.Instance.AllDoors)
                {
                    if (door == null) continue;
                    try
                    {
                        ShipStatus.Instance.RpcUpdateSystem(SystemTypes.Doors, (byte)door.Id);
                    }
                    catch { }
                }
            }
        }
        catch { }
    }

    private static void OpenDoorsForRoom(SystemTypes room)
    {
        try
        {
            if (ShipStatus.Instance?.AllDoors == null) return;
            foreach (var door in ShipStatus.Instance.AllDoors)
            {
                if (door == null) continue;
                try
                {
                    if (door.Room == room)
                        ShipStatus.Instance.RpcUpdateSystem(SystemTypes.Doors, (byte)door.Id);
                }
                catch { }
            }
        }
        catch { }
    }

    private static void DoSabotage(SystemTypes sys)
    {
        try
        {
            if (ShipStatus.Instance == null) return;
            ShipStatus.Instance.RpcUpdateSystem(sys, 128);
        }
        catch { }
    }

    private static void SabotageLights()
    {
        try
        {
            if (ShipStatus.Instance == null) return;
            // Flip all 5 light switches to sabotage (each switch = index | 128)
            for (byte i = 0; i < 5; i++)
                ShipStatus.Instance.RpcUpdateSystem(SystemTypes.Electrical, (byte)(i | 128));
        }
        catch { }
    }
    private static void SabotageReactor() => DoSabotage(SystemTypes.Reactor);
    private static void SabotageO2() => DoSabotage(SystemTypes.LifeSupp);
    private static void SabotageComms() => DoSabotage(SystemTypes.Comms);

    private static void FixSabotages()
    {
        try { foreach (var s in new[] { SystemTypes.Electrical, SystemTypes.Reactor, SystemTypes.LifeSupp, SystemTypes.Comms }) { try { ShipStatus.Instance.RpcUpdateSystem(s, 16); ShipStatus.Instance.RpcUpdateSystem(s, 64); } catch { } } } catch { }
    }

    private static void ForceEndGame()
    {
        try
        {
            // Complete all of our own tasks via RPC to push task bar to completion
            var local = PlayerControl.LocalPlayer;
            for (int i = 0; i < local.myTasks.Count; i++)
            {
                var t = local.myTasks[i];
                if (t != null && !t.IsComplete)
                    try { local.RpcCompleteTask(t.Id); } catch { }
            }
        }
        catch { }
    }

    // Chat - FIXED: properly sends one message
    private static void SendChat(string msg)
    {
        try
        {
            var chat = HudManager.Instance?.Chat;
            if (chat == null) return;
            chat.timeSinceLastMessage = 10f;
            var ta = chat.GetComponentInChildren<TMPro.TMP_InputField>();
            if (ta != null)
            {
                ta.text = "";
                ta.text = msg;
                chat.SendChat();
            }
        }
        catch { }
    }

    private static void SendVoteRandom()
    {
        try
        {
            foreach (var p in PlayerControl.AllPlayerControls)
            {
                if (p == null || p == PlayerControl.LocalPlayer || p.Data == null || p.Data.IsDead) continue;
                SendChat($"Vote {p.Data.PlayerName}! They're sus!");
                return;
            }
        }
        catch { }
    }

    private static void SetName(string n) { try { PlayerControl.LocalPlayer.RpcSetName(n); } catch { } }
    private static void ApplyForceColor() { try { PlayerControl.LocalPlayer.RpcSetColor((byte)ForceColorId); } catch { } }
    private static void RandomizeColor() { try { PlayerControl.LocalPlayer.RpcSetColor((byte)UnityEngine.Random.Range(0, 18)); } catch { } }
    private static string GetColorName(int id) => id >= 0 && id < ColorNames.Length ? ColorNames[id] : $"#{id}";

    // Cosmetics
    private static void CycleHat(int d) { try { var h = HatManager.Instance.allHats; if (h.Length > 0) { _hatIdx = (_hatIdx + d + h.Length) % h.Length; SetHat(h[_hatIdx].ProdId); } } catch { } }
    private static void CycleSkin(int d) { try { var s = HatManager.Instance.allSkins; if (s.Length > 0) { _skinIdx = (_skinIdx + d + s.Length) % s.Length; SetSkinId(s[_skinIdx].ProdId); } } catch { } }
    private static void CycleVisor(int d) { try { var v = HatManager.Instance.allVisors; if (v.Length > 0) { _visorIdx = (_visorIdx + d + v.Length) % v.Length; SetVisorId(v[_visorIdx].ProdId); } } catch { } }
    private static void CyclePet(int d) { try { var p = HatManager.Instance.allPets; if (p.Length > 0) { _petIdx = (_petIdx + d + p.Length) % p.Length; SetPetId(p[_petIdx].ProdId); } } catch { } }
    private static void RandomHat() { try { var h = HatManager.Instance.allHats; if (h.Length > 0) SetHat(h[UnityEngine.Random.Range(0, h.Length)].ProdId); } catch { } }
    private static void RandomSkin() { try { var s = HatManager.Instance.allSkins; if (s.Length > 0) SetSkinId(s[UnityEngine.Random.Range(0, s.Length)].ProdId); } catch { } }
    private static void RandomVisor() { try { var v = HatManager.Instance.allVisors; if (v.Length > 0) SetVisorId(v[UnityEngine.Random.Range(0, v.Length)].ProdId); } catch { } }
    private static void RandomPet() { try { var p = HatManager.Instance.allPets; if (p.Length > 0) SetPetId(p[UnityEngine.Random.Range(0, p.Length)].ProdId); } catch { } }
    private static void SetHat(string id) { try { PlayerControl.LocalPlayer.RpcSetHat(id); } catch { } }
    private static void SetSkinId(string id) { try { PlayerControl.LocalPlayer.RpcSetSkin(id); } catch { } }
    private static void SetVisorId(string id) { try { PlayerControl.LocalPlayer.RpcSetVisor(id); } catch { } }
    private static void SetPetId(string id) { try { PlayerControl.LocalPlayer.RpcSetPet(id); } catch { } }

    private static PlayerControl GetNearest()
    {
        var local = PlayerControl.LocalPlayer;
        if (local == null) return null;
        PlayerControl best = null; float min = float.MaxValue;
        foreach (var p in PlayerControl.AllPlayerControls)
        {
            if (p == null || p == local || p.Data == null || p.Data.IsDead || p.Data.Disconnected) continue;
            float d = Vector2.Distance(local.GetTruePosition(), p.GetTruePosition());
            if (d < min) { min = d; best = p; }
        }
        return best;
    }
}

// ══════════════════════════════════════
//  HARMONY PATCHES
// ══════════════════════════════════════

[HarmonyPatch(typeof(ShipStatus), nameof(ShipStatus.CalculateLightRadius))]
public static class FullVisionPatch
{
    public static bool Prefix(ref float __result) { try { if (HackMenu.FullVisionEnabled) { __result = 100f; return false; } } catch { } return true; }
}

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.SetKillTimer))]
public static class ZeroCooldownPatch
{
    public static bool Prefix(ref float time) { try { if (HackMenu.ZeroCooldownEnabled) time = 0f; } catch { } return true; }
}

[HarmonyPatch(typeof(Vent), nameof(Vent.CanUse))]
public static class VentAsCrewmatePatch
{
    public static void Postfix(ref float __result, ref bool canUse, ref bool couldUse)
    {
        try { if (HackMenu.VentAsCrewmateEnabled && PlayerControl.LocalPlayer != null) { canUse = true; couldUse = true; __result = 0f; } } catch { }
    }
}

[HarmonyPatch(typeof(RoleBehaviour), nameof(RoleBehaviour.CanVent), MethodType.Getter)]
public static class RoleCanVentPatch
{
    public static void Postfix(ref bool __result)
    {
        try { if (HackMenu.VentAsCrewmateEnabled) __result = true; } catch { }
    }
}

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.CmdCheckMurder))]
public static class InfiniteKillRangePatch
{
    public static void Prefix(PlayerControl __instance)
    {
        try { if (HackMenu.InfiniteKillRangeEnabled && __instance == PlayerControl.LocalPlayer) __instance.MaxReportDistance = 9999f; } catch { }
    }
}

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.Die))]
public static class GodModePatch
{
    public static bool Prefix(PlayerControl __instance)
    {
        try { if ((HackMenu.GodModeEnabled || HackMenu.AntiKillEnabled) && __instance == PlayerControl.LocalPlayer) return false; } catch { }
        return true;
    }
}

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.Exiled))]
public static class AntiExilePatch
{
    public static bool Prefix(PlayerControl __instance)
    {
        try { if (HackMenu.GodModeEnabled && __instance == PlayerControl.LocalPlayer) return false; } catch { }
        return true;
    }
}

[HarmonyPatch(typeof(CosmeticData), nameof(CosmeticData.Free), MethodType.Getter)]
public static class UnlockCosmeticsPatch
{
    public static void Postfix(ref bool __result) { try { if (HackMenu.UnlockAllCosmeticsEnabled) __result = true; } catch { } }
}

[HarmonyPatch(typeof(CosmeticData), nameof(CosmeticData.NotInStore), MethodType.Getter)]
public static class NotInStorePatch
{
    public static void Postfix(ref bool __result) { try { if (HackMenu.UnlockAllCosmeticsEnabled) __result = false; } catch { } }
}

using System;
using HarmonyLib;
using UnityEngine;

namespace CustomMod.Features;

[HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
public static class ZoomOutPatch
{
    private static float _currentZoom = 3f;

    public static void Postfix(HudManager __instance)
    {
        try
        {
            if (!CustomModPlugin.EnableZoomOut.Value) return;

            var cam = Camera.main;
            if (cam == null) return;

            float scroll = UnityEngine.Input.GetAxis("Mouse ScrollWheel");
            if (scroll != 0f)
            {
                _currentZoom -= scroll * 2f;
                _currentZoom = Mathf.Clamp(_currentZoom, 3f, 12f);
            }

            cam.orthographicSize = Mathf.Lerp(cam.orthographicSize, _currentZoom, Time.deltaTime * 8f);
        }
        catch (Exception) { }
    }
}

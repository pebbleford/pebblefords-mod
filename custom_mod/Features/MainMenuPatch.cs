using System;
using HarmonyLib;
using UnityEngine;

namespace CustomMod.Features;

/// <summary>
/// Patches the main menu to show "Pebbleford's Mod" branding.
/// </summary>
[HarmonyPatch(typeof(MainMenuManager), nameof(MainMenuManager.Start))]
public static class MainMenuPatch
{
    public static void Postfix(MainMenuManager __instance)
    {
        try
        {
            // Find the version text and add our mod name
            var versionShower = GameObject.FindObjectOfType<VersionShower>();
            if (versionShower != null && versionShower.text != null)
            {
                var original = versionShower.text.text;
                versionShower.text.text = "<color=#ff6b6b>Pebbleford's Mod</color> <color=#aaa>v1.0.0</color>\n" + original;
            }

            // Add a title banner at the top
            var canvas = __instance.gameObject;
            var bannerGo = new GameObject("PebblefordBanner");
            bannerGo.transform.SetParent(canvas.transform, false);
            bannerGo.transform.localPosition = new Vector3(0f, 2.8f, -10f);

            var bannerText = bannerGo.AddComponent<TMPro.TextMeshPro>();
            bannerText.text = "<color=#ff6b6b>PEBBLEFORD'S</color> <color=#ffffff>MOD</color>";
            bannerText.fontSize = 3.5f;
            bannerText.alignment = TMPro.TextAlignmentOptions.Center;
            bannerText.fontStyle = TMPro.FontStyles.Bold;
            bannerText.outlineWidth = 0.2f;
            bannerText.outlineColor = new Color32(0, 0, 0, 255);

            // Add subtitle with controls hint
            var hintGo = new GameObject("PebblefordHint");
            hintGo.transform.SetParent(canvas.transform, false);
            hintGo.transform.localPosition = new Vector3(0f, 2.35f, -10f);

            var hintText = hintGo.AddComponent<TMPro.TextMeshPro>();
            hintText.text = "<color=#888>Press INSERT to open hack menu</color>";
            hintText.fontSize = 1.5f;
            hintText.alignment = TMPro.TextAlignmentOptions.Center;
            hintText.outlineWidth = 0.1f;
            hintText.outlineColor = new Color32(0, 0, 0, 255);
        }
        catch (Exception) { }
    }
}

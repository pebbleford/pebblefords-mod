using System;
using System.Collections.Generic;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;

namespace CustomMod.Features;

/// <summary>
/// Adds Pebbleford's Mod settings to the actual game settings menu.
/// Patches GameOptionsMenu.CreateSettings to add toggle options for roles/features.
/// Uses the game's own checkboxOrigin template for native-looking toggles.
/// </summary>
[HarmonyPatch(typeof(GameOptionsMenu), nameof(GameOptionsMenu.CreateSettings))]
public static class GameSettingsTabPatch
{
    private static List<GameObject> _createdObjects = new();

    public static void Postfix(GameOptionsMenu __instance)
    {
        try
        {
            // Clean up previously created objects
            foreach (var go in _createdObjects)
            {
                if (go != null)
                    UnityEngine.Object.Destroy(go);
            }
            _createdObjects.Clear();

            // Use the game's own checkbox template
            var template = __instance.checkboxOrigin;
            if (template == null) return;

            // Use settingsContainer as parent, fall back to template's parent
            var parent = __instance.settingsContainer != null
                ? __instance.settingsContainer
                : template.transform.parent;

            // Find the lowest Y position of existing options to place ours below
            float lowestY = 0f;
            var children = __instance.Children;
            if (children != null)
            {
                foreach (var opt in children)
                {
                    if (opt != null && opt.transform.localPosition.y < lowestY)
                        lowestY = opt.transform.localPosition.y;
                }
            }

            float y = lowestY - 0.8f;
            float spacing = -0.45f;

            // ── Header ──
            var headerGo = new GameObject("PebblefordHeader");
            headerGo.transform.SetParent(parent, false);
            headerGo.transform.localPosition = new Vector3(0.1f, y, -2f);
            var headerTmp = headerGo.AddComponent<TMPro.TextMeshPro>();
            headerTmp.text = "<color=#ff6b6b>── PEBBLEFORD'S MOD ──</color>";
            headerTmp.fontSize = 2.8f;
            headerTmp.fontStyle = TMPro.FontStyles.Bold;
            headerTmp.alignment = TMPro.TextAlignmentOptions.Center;
            headerTmp.outlineWidth = 0.15f;
            headerTmp.outlineColor = Color.black;
            headerTmp.rectTransform.sizeDelta = new Vector2(5f, 0.5f);
            _createdObjects.Add(headerGo);
            y += spacing;

            // ── Role Toggles ──
            CreateModToggle(template, parent, "Mod_Sheriff", "Sheriff Role", CustomModPlugin.EnableSheriff, ref y, spacing);
            CreateModToggle(template, parent, "Mod_Jester", "Jester Role", CustomModPlugin.EnableJester, ref y, spacing);
            CreateModToggle(template, parent, "Mod_Mayor", "Mayor Role", CustomModPlugin.EnableMayor, ref y, spacing);
            CreateModToggle(template, parent, "Mod_Seer", "Seer Role", CustomModPlugin.EnableSeer, ref y, spacing);

            // ── Feature Toggles ──
            y += spacing * 0.5f;
            CreateModToggle(template, parent, "Mod_SpeedBoost", "Speed Boost", CustomModPlugin.EnableSpeedBoost, ref y, spacing);
            CreateModToggle(template, parent, "Mod_ZoomOut", "Zoom Out", CustomModPlugin.EnableZoomOut, ref y, spacing);
            CreateModToggle(template, parent, "Mod_ShowNames", "Always Show Names", CustomModPlugin.AlwaysShowNames, ref y, spacing);
            CreateModToggle(template, parent, "Mod_ChaosMode", "Chaos Mode", CustomModPlugin.EnableChaosMode, ref y, spacing);
            CreateModToggle(template, parent, "Mod_GameInfo", "Game Info HUD", CustomModPlugin.EnableGameInfo, ref y, spacing);
        }
        catch (Exception) { }
    }

    private static void CreateModToggle(ToggleOption template, Transform parent, string name, string title, ConfigEntry<bool> config, ref float y, float spacing)
    {
        try
        {
            var toggle = UnityEngine.Object.Instantiate(template, parent);
            toggle.name = name;
            toggle.transform.localPosition = new Vector3(template.transform.localPosition.x, y, template.transform.localPosition.z);
            y += spacing;

            if (toggle.TitleText != null)
                toggle.TitleText.text = title;

            if (toggle.CheckMark != null)
                toggle.CheckMark.enabled = config.Value;

            _createdObjects.Add(toggle.gameObject);
        }
        catch { }
    }
}

/// <summary>
/// Intercepts clicks on our custom toggle options to update config values
/// instead of letting the game try to map them to game settings.
/// </summary>
[HarmonyPatch(typeof(ToggleOption), nameof(ToggleOption.Toggle))]
public static class ModToggleClickPatch
{
    public static bool Prefix(ToggleOption __instance)
    {
        try
        {
            if (__instance == null || __instance.name == null) return true;
            if (!__instance.name.StartsWith("Mod_")) return true;

            bool newVal = false;

            switch (__instance.name)
            {
                case "Mod_Sheriff":
                    newVal = !CustomModPlugin.EnableSheriff.Value;
                    CustomModPlugin.EnableSheriff.Value = newVal;
                    break;
                case "Mod_Jester":
                    newVal = !CustomModPlugin.EnableJester.Value;
                    CustomModPlugin.EnableJester.Value = newVal;
                    break;
                case "Mod_Mayor":
                    newVal = !CustomModPlugin.EnableMayor.Value;
                    CustomModPlugin.EnableMayor.Value = newVal;
                    break;
                case "Mod_Seer":
                    newVal = !CustomModPlugin.EnableSeer.Value;
                    CustomModPlugin.EnableSeer.Value = newVal;
                    break;
                case "Mod_SpeedBoost":
                    newVal = !CustomModPlugin.EnableSpeedBoost.Value;
                    CustomModPlugin.EnableSpeedBoost.Value = newVal;
                    break;
                case "Mod_ZoomOut":
                    newVal = !CustomModPlugin.EnableZoomOut.Value;
                    CustomModPlugin.EnableZoomOut.Value = newVal;
                    break;
                case "Mod_ShowNames":
                    newVal = !CustomModPlugin.AlwaysShowNames.Value;
                    CustomModPlugin.AlwaysShowNames.Value = newVal;
                    break;
                case "Mod_ChaosMode":
                    newVal = !CustomModPlugin.EnableChaosMode.Value;
                    CustomModPlugin.EnableChaosMode.Value = newVal;
                    break;
                case "Mod_GameInfo":
                    newVal = !CustomModPlugin.EnableGameInfo.Value;
                    CustomModPlugin.EnableGameInfo.Value = newVal;
                    break;
                default:
                    return true;
            }

            if (__instance.CheckMark != null)
                __instance.CheckMark.enabled = newVal;

            return false; // Skip original toggle behavior
        }
        catch { }
        return true;
    }
}

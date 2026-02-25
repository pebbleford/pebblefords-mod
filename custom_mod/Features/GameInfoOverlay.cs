using System;
using HarmonyLib;
using UnityEngine;
using CustomMod.Roles;

namespace CustomMod.Features;

[HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
public static class GameInfoOverlayPatch
{
    private static TMPro.TextMeshPro _infoText;

    public static void Postfix(HudManager __instance)
    {
        try
        {
            if (__instance == null) return;

            if (_infoText == null)
            {
                var go = new GameObject("CustomModInfo");
                go.transform.SetParent(__instance.transform, false);
                go.transform.localPosition = new Vector3(-4.5f, 2.5f, -10f);
                _infoText = go.AddComponent<TMPro.TextMeshPro>();
                _infoText.fontSize = 1.6f;
                _infoText.alignment = TMPro.TextAlignmentOptions.TopLeft;
                _infoText.fontStyle = TMPro.FontStyles.Bold;
                _infoText.outlineWidth = 0.15f;
                _infoText.outlineColor = Color.black;
            }

            if (!ShipStatus.Instance || PlayerControl.LocalPlayer == null)
            {
                if (_infoText != null) _infoText.text = "";
                return;
            }

            string text = "";

            var role = CustomRoleManager.GetLocalRole();
            if (role != CustomRole.None)
            {
                var color = CustomRoleManager.GetRoleColor(role);
                text += $"<color=#{ColorUtility.ToHtmlStringRGB(color)}>{CustomRoleManager.GetRoleName(role)}</color>\n";
            }

            if (CustomModPlugin.EnableGameInfo.Value)
            {
                int alive = 0, dead = 0;
                if (GameData.Instance != null)
                {
                    foreach (var data in GameData.Instance.AllPlayers)
                    {
                        if (data == null || data.Disconnected) continue;
                        if (data.IsDead) dead++;
                        else alive++;
                    }
                }
                text += $"<color=#aaa>Alive: {alive} | Dead: {dead}</color>\n";
            }

            var seerText = SeerPatches.GetRevealText();
            if (seerText != null)
                text += $"\n{seerText}\n";

            if (role == CustomRole.Sheriff)
            {
                if (CustomRoleManager.SheriffKillTimer > 0)
                    text += $"\n<color=#ff0>Kill CD: {CustomRoleManager.SheriffKillTimer:F0}s</color>\n";
                else
                    text += $"\n<color=#0f0>Press Q to kill!</color>\n";
            }

            if (role == CustomRole.Seer)
                text += $"\n<color=#5cf>Press F near a player to reveal</color>\n";

            var chaos = ChaosModePatch.CurrentEffect;
            if (chaos != null)
                text += $"\n<color=#f55>{chaos}</color>\n";

            if (CustomRoleManager.JesterWon)
                text += $"\n<color=#e55ef7>JESTER WINS!</color>\n";

            _infoText.text = text;
        }
        catch (Exception) { }
    }
}

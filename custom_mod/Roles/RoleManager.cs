using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using UnityEngine;

namespace CustomMod.Roles;

public enum CustomRole
{
    None,
    Sheriff,
    Jester,
    Mayor,
    Seer
}

public static class CustomRoleManager
{
    public static Dictionary<byte, CustomRole> PlayerRoles = new();
    public static HashSet<byte> SeerChecked = new();
    public static float SheriffKillTimer = 0f;
    public static float SheriffKillCooldown = 25f;
    public static bool JesterWon = false;

    public static void Reset()
    {
        PlayerRoles.Clear();
        SeerChecked.Clear();
        SheriffKillTimer = 0f;
        JesterWon = false;
    }

    public static CustomRole GetRole(byte playerId)
    {
        return PlayerRoles.TryGetValue(playerId, out var role) ? role : CustomRole.None;
    }

    public static CustomRole GetLocalRole()
    {
        if (PlayerControl.LocalPlayer == null) return CustomRole.None;
        return GetRole(PlayerControl.LocalPlayer.PlayerId);
    }

    public static string GetRoleName(CustomRole role) => role switch
    {
        CustomRole.Sheriff => "Sheriff",
        CustomRole.Jester => "Jester",
        CustomRole.Mayor => "Mayor",
        CustomRole.Seer => "Seer",
        _ => ""
    };

    public static Color GetRoleColor(CustomRole role) => role switch
    {
        CustomRole.Sheriff => new Color(1f, 0.8f, 0f),
        CustomRole.Jester => new Color(0.9f, 0.3f, 0.9f),
        CustomRole.Mayor => new Color(0.3f, 0.6f, 0.3f),
        CustomRole.Seer => new Color(0.3f, 0.8f, 1f),
        _ => Color.white
    };
}

[HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.CoBegin))]
public static class AssignRolesPatch
{
    public static void Postfix()
    {
        try
        {
            CustomRoleManager.Reset();

            if (AmongUsClient.Instance == null || !AmongUsClient.Instance.AmHost) return;

            var allPlayers = PlayerControl.AllPlayerControls.ToArray()
                .Where(p => p != null && p.Data != null && p.Data.Role != null && !p.Data.Role.IsImpostor)
                .ToList();

            if (allPlayers.Count < 2) return;

            var rng = new System.Random();
            var shuffled = allPlayers.OrderBy(_ => rng.Next()).ToList();
            int idx = 0;

            if (CustomModPlugin.EnableSheriff.Value && idx < shuffled.Count)
            {
                CustomRoleManager.PlayerRoles[shuffled[idx].PlayerId] = CustomRole.Sheriff;
                idx++;
            }
            if (CustomModPlugin.EnableJester.Value && idx < shuffled.Count)
            {
                CustomRoleManager.PlayerRoles[shuffled[idx].PlayerId] = CustomRole.Jester;
                idx++;
            }
            if (CustomModPlugin.EnableMayor.Value && idx < shuffled.Count)
            {
                CustomRoleManager.PlayerRoles[shuffled[idx].PlayerId] = CustomRole.Mayor;
                idx++;
            }
            if (CustomModPlugin.EnableSeer.Value && idx < shuffled.Count)
            {
                CustomRoleManager.PlayerRoles[shuffled[idx].PlayerId] = CustomRole.Seer;
                idx++;
            }
        }
        catch (Exception) { }
    }
}

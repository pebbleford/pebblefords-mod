using System;
using HarmonyLib;
using UnityEngine;

namespace CustomMod.Roles;

public static class SheriffPatches
{
    public static void TrySheriffKill()
    {
        try
        {
            if (!CustomModPlugin.EnableSheriff.Value) return;
            if (CustomRoleManager.GetLocalRole() != CustomRole.Sheriff) return;
            if (CustomRoleManager.SheriffKillTimer > 0f) return;

            var local = PlayerControl.LocalPlayer;
            if (local == null || local.Data == null || local.Data.IsDead) return;
            if (!ShipStatus.Instance) return;

            PlayerControl target = null;
            float closestDist = float.MaxValue;
            float killDist = 1.5f;
            try { killDist = GameOptionsManager.Instance.currentNormalGameOptions.KillDistance; } catch { }

            foreach (var player in PlayerControl.AllPlayerControls)
            {
                if (player == null || player.PlayerId == local.PlayerId) continue;
                if (player.Data == null || player.Data.IsDead) continue;

                float dist = Vector2.Distance(local.GetTruePosition(), player.GetTruePosition());
                if (dist < killDist && dist < closestDist)
                {
                    closestDist = dist;
                    target = player;
                }
            }

            if (target == null) return;

            if (target.Data.Role != null && target.Data.Role.IsImpostor)
                local.MurderPlayer(target, MurderResultFlags.Succeeded);
            else
                local.MurderPlayer(local, MurderResultFlags.Succeeded);

            CustomRoleManager.SheriffKillTimer = CustomRoleManager.SheriffKillCooldown;
        }
        catch (Exception) { }
    }
}

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.FixedUpdate))]
public static class SheriffCooldownPatch
{
    public static void Postfix(PlayerControl __instance)
    {
        try
        {
            if (__instance != PlayerControl.LocalPlayer) return;
            if (CustomRoleManager.GetLocalRole() != CustomRole.Sheriff) return;
            if (!ShipStatus.Instance) return;

            if (CustomRoleManager.SheriffKillTimer > 0f)
                CustomRoleManager.SheriffKillTimer -= Time.fixedDeltaTime;

            if (UnityEngine.Input.GetKeyDown(KeyCode.Q))
                SheriffPatches.TrySheriffKill();
        }
        catch (Exception) { }
    }
}

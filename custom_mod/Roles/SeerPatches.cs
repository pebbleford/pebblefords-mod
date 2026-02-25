using System;
using HarmonyLib;
using UnityEngine;

namespace CustomMod.Roles;

public static class SeerPatches
{
    private static string _lastReveal = "";
    private static float _revealTimer = 0f;

    public static void TrySeerReveal()
    {
        try
        {
            if (!CustomModPlugin.EnableSeer.Value) return;
            if (CustomRoleManager.GetLocalRole() != CustomRole.Seer) return;

            var local = PlayerControl.LocalPlayer;
            if (local == null || local.Data == null || local.Data.IsDead) return;
            if (!ShipStatus.Instance) return;

            PlayerControl target = null;
            float closestDist = float.MaxValue;

            foreach (var player in PlayerControl.AllPlayerControls)
            {
                if (player == null || player.PlayerId == local.PlayerId) continue;
                if (player.Data == null || player.Data.IsDead) continue;

                float dist = Vector2.Distance(local.GetTruePosition(), player.GetTruePosition());
                if (dist < 2f && dist < closestDist)
                {
                    closestDist = dist;
                    target = player;
                }
            }

            if (target == null) return;

            if (CustomRoleManager.SeerChecked.Contains(target.PlayerId))
            {
                _lastReveal = $"{target.Data.PlayerName}: Already checked!";
                _revealTimer = 3f;
                return;
            }

            CustomRoleManager.SeerChecked.Add(target.PlayerId);

            string roleText;
            if (target.Data.Role != null && target.Data.Role.IsImpostor)
                roleText = "IMPOSTOR";
            else
            {
                var custom = CustomRoleManager.GetRole(target.PlayerId);
                if (custom != CustomRole.None)
                    roleText = CustomRoleManager.GetRoleName(custom);
                else
                    roleText = "Crewmate";
            }

            _lastReveal = $"{target.Data.PlayerName} is {roleText}";
            _revealTimer = 5f;
        }
        catch (Exception) { }
    }

    public static string GetRevealText()
    {
        if (_revealTimer > 0f) return _lastReveal;
        return null;
    }

    public static void UpdateTimer()
    {
        if (_revealTimer > 0f) _revealTimer -= Time.deltaTime;
    }
}

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.FixedUpdate))]
public static class SeerUpdatePatch
{
    public static void Postfix(PlayerControl __instance)
    {
        try
        {
            if (__instance != PlayerControl.LocalPlayer) return;
            if (CustomRoleManager.GetLocalRole() != CustomRole.Seer) return;
            if (!ShipStatus.Instance) return;

            SeerPatches.UpdateTimer();

            if (UnityEngine.Input.GetKeyDown(KeyCode.F))
                SeerPatches.TrySeerReveal();
        }
        catch (Exception) { }
    }
}

using System;
using HarmonyLib;

namespace CustomMod.Features;

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.FixedUpdate))]
public static class SpeedBoostPatch
{
    public static void Postfix(PlayerControl __instance)
    {
        try
        {
            if (!CustomModPlugin.EnableSpeedBoost.Value) return;
            if (__instance != PlayerControl.LocalPlayer) return;
            if (__instance.Data == null || __instance.Data.IsDead) return;
            if (!ShipStatus.Instance) return;

            var physics = __instance.MyPhysics;
            if (physics == null) return;

            float baseSpeed = 1f;
            try { baseSpeed = GameOptionsManager.Instance.currentNormalGameOptions.PlayerSpeedMod; } catch { }
            physics.Speed = baseSpeed * CustomModPlugin.SpeedMultiplier.Value;
        }
        catch (Exception) { }
    }
}

using System;
using HarmonyLib;

namespace CustomMod.Features;

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.FixedUpdate))]
public static class AlwaysShowNamesPatch
{
    public static void Postfix(PlayerControl __instance)
    {
        try
        {
            if (!CustomModPlugin.AlwaysShowNames.Value) return;
            if (__instance == null || __instance.cosmetics == null) return;
            if (__instance.Data == null || __instance.Data.IsDead) return;
            if (!ShipStatus.Instance) return;

            var nameText = __instance.cosmetics.nameText;
            if (nameText != null)
                nameText.gameObject.SetActive(true);
        }
        catch (Exception) { }
    }
}

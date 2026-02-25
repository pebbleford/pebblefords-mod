using System;
using HarmonyLib;

namespace CustomMod.Roles;

[HarmonyPatch(typeof(ExileController), nameof(ExileController.WrapUp))]
public static class JesterExilePatch
{
    public static void Postfix(ExileController __instance)
    {
        try
        {
            if (!CustomModPlugin.EnableJester.Value) return;
            if (__instance == null || __instance.initData == null) return;

            var exiled = __instance.initData.networkedPlayer;
            if (exiled == null) return;

            var role = CustomRoleManager.GetRole(exiled.PlayerId);
            if (role == CustomRole.Jester)
            {
                CustomRoleManager.JesterWon = true;

                if (AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost)
                {
                    foreach (var player in PlayerControl.AllPlayerControls)
                    {
                        if (player != null && player.Data != null && !player.Data.IsDead && player.PlayerId != exiled.PlayerId)
                        {
                            player.MurderPlayer(player, MurderResultFlags.Succeeded);
                        }
                    }
                }
            }
        }
        catch (Exception) { }
    }
}

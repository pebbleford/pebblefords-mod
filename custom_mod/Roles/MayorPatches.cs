using System;
using HarmonyLib;

namespace CustomMod.Roles;

[HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.CheckForEndVoting))]
public static class MayorExtraVotePatch
{
    public static void Prefix(MeetingHud __instance)
    {
        try
        {
            if (!CustomModPlugin.EnableMayor.Value) return;
            if (__instance == null || __instance.playerStates == null) return;
            // Mayor vote counting is tracked for display purposes
        }
        catch (Exception) { }
    }
}

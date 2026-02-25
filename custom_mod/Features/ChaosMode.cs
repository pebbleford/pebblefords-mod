using System;
using HarmonyLib;
using UnityEngine;

namespace CustomMod.Features;

[HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.FixedUpdate))]
public static class ChaosModePatch
{
    private static float _eventTimer = 30f;
    private static float _effectTimer = 0f;
    private static string _currentEffect = "";
    private static float _savedSpeed = 0f;

    public static string CurrentEffect => _effectTimer > 0 ? _currentEffect : null;

    public static void Postfix(PlayerControl __instance)
    {
        try
        {
            if (!CustomModPlugin.EnableChaosMode.Value) return;
            if (__instance != PlayerControl.LocalPlayer) return;
            if (__instance.Data == null || __instance.Data.IsDead) return;
            if (!ShipStatus.Instance) return;

            if (_effectTimer > 0f)
            {
                _effectTimer -= Time.fixedDeltaTime;
                if (_effectTimer <= 0f)
                    EndEffect(__instance);
            }

            _eventTimer -= Time.fixedDeltaTime;
            if (_eventTimer <= 0f)
            {
                _eventTimer = CustomModPlugin.ChaosInterval.Value;
                TriggerRandomEvent(__instance);
            }
        }
        catch (Exception) { }
    }

    private static void TriggerRandomEvent(PlayerControl player)
    {
        try
        {
            int eventType = UnityEngine.Random.Range(0, 3);

            switch (eventType)
            {
                case 0:
                    if (player.MyPhysics != null)
                    {
                        _savedSpeed = player.MyPhysics.Speed;
                        player.MyPhysics.Speed = UnityEngine.Random.Range(0.5f, 3.5f);
                        _currentEffect = $"CHAOS: Speed Shuffle!";
                        _effectTimer = 8f;
                    }
                    break;

                case 1:
                    if (ShipStatus.Instance != null && ShipStatus.Instance.AllVents != null)
                    {
                        var vents = ShipStatus.Instance.AllVents;
                        if (vents.Count > 0)
                        {
                            var vent = vents[UnityEngine.Random.Range(0, vents.Count)];
                            if (vent != null)
                            {
                                player.NetTransform.RpcSnapTo(vent.transform.position);
                                _currentEffect = "CHAOS: Teleported!";
                                _effectTimer = 3f;
                            }
                        }
                    }
                    break;

                case 2:
                    _currentEffect = "CHAOS: Lights flickering!";
                    _effectTimer = 5f;
                    break;
            }
        }
        catch (Exception) { }
    }

    private static void EndEffect(PlayerControl player)
    {
        try
        {
            if (_savedSpeed > 0 && player.MyPhysics != null)
            {
                player.MyPhysics.Speed = _savedSpeed;
                _savedSpeed = 0;
            }
            _currentEffect = "";
        }
        catch (Exception) { }
    }
}

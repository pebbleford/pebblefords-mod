using BepInEx;
using BepInEx.Configuration;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;

namespace CustomMod;

[BepInPlugin("com.pebbleford.mod", "Pebblefords Mod", "1.0.0")]
[BepInProcess("Among Us.exe")]
public class CustomModPlugin : BasePlugin
{
    public static CustomModPlugin Instance { get; private set; }
    public Harmony Harmony { get; private set; }

    // ── Config entries (toggles) ──
    public static ConfigEntry<bool> EnableSheriff;
    public static ConfigEntry<bool> EnableJester;
    public static ConfigEntry<bool> EnableMayor;
    public static ConfigEntry<bool> EnableSeer;
    public static ConfigEntry<bool> EnableSpeedBoost;
    public static ConfigEntry<float> SpeedMultiplier;
    public static ConfigEntry<bool> EnableZoomOut;
    public static ConfigEntry<float> ZoomLevel;
    public static ConfigEntry<bool> AlwaysShowNames;
    public static ConfigEntry<bool> EnableChaosMode;
    public static ConfigEntry<float> ChaosInterval;
    public static ConfigEntry<bool> EnableGameInfo;

    public override void Load()
    {
        Instance = this;

        // ── Roles ──
        EnableSheriff = Config.Bind("Roles", "EnableSheriff", true,
            "Sheriff: A crewmate who can kill. Kills impostors = success, kills crew = sheriff dies.");
        EnableJester = Config.Bind("Roles", "EnableJester", true,
            "Jester: Wins if voted out during a meeting. Appears as crewmate.");
        EnableMayor = Config.Bind("Roles", "EnableMayor", true,
            "Mayor: Has a double vote during meetings.");
        EnableSeer = Config.Bind("Roles", "EnableSeer", true,
            "Seer: Can see the role of one player per round.");

        // ── Fun / Chaos ──
        EnableChaosMode = Config.Bind("Chaos", "EnableChaosMode", false,
            "Chaos Mode: Random events happen periodically.");
        ChaosInterval = Config.Bind("Chaos", "ChaosInterval", 30f,
            "Seconds between random chaos events.");

        // ── Utility / QOL ──
        EnableSpeedBoost = Config.Bind("Utility", "EnableSpeedBoost", false,
            "Speed Boost: Increase player movement speed.");
        SpeedMultiplier = Config.Bind("Utility", "SpeedMultiplier", 1.5f,
            "Speed multiplier (1.0 = normal, 2.0 = double speed).");
        EnableZoomOut = Config.Bind("Utility", "EnableZoomOut", false,
            "Zoom Out: Press mouse scroll to zoom camera in/out.");
        ZoomLevel = Config.Bind("Utility", "ZoomLevel", 6f,
            "Default zoom level (3 = normal, 6 = zoomed out).");
        AlwaysShowNames = Config.Bind("Utility", "AlwaysShowNames", false,
            "Always show player names even at a distance.");
        EnableGameInfo = Config.Bind("Utility", "EnableGameInfo", false,
            "Show game info overlay (player count, alive/dead, tasks).");

        // Register and create hack menu component
        ClassInjector.RegisterTypeInIl2Cpp<Features.HackMenu>();
        var hackMenuGo = new GameObject("PebblefordHackMenu");
        hackMenuGo.hideFlags = HideFlags.HideAndDontSave;
        UnityEngine.Object.DontDestroyOnLoad(hackMenuGo);
        hackMenuGo.AddComponent<Features.HackMenu>();

        Harmony = new Harmony("com.pebbleford.mod");
        Harmony.PatchAll();

        Log.LogInfo("Pebbleford's Mod loaded! Press INSERT to open hack menu.");
    }
}

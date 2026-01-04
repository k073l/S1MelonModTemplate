using System.Collections;
using MelonLoader;
using MyMod.Helpers;
using UnityEngine;
//-:cnd:noEmit
#if MONO
using FishNet;
#else
using Il2CppFishNet;
#endif
//+:cnd:noEmit

[assembly: MelonInfo(
    typeof(MyMod.MyMod),
    MyMod.BuildInfo.Name,
    MyMod.BuildInfo.Version,
    MyMod.BuildInfo.Author
)]
[assembly: MelonColor(1, 255, 0, 0)]
[assembly: MelonGame("TVGS", "Schedule I")]

//-:cnd:noEmit
// Specify platform domain based on build target (remove this if your mod supports both via S1API)
#if MONO
[assembly: MelonPlatformDomain(MelonPlatformDomainAttribute.CompatibleDomains.MONO)]
#else
[assembly: MelonPlatformDomain(MelonPlatformDomainAttribute.CompatibleDomains.IL2CPP)]
#endif
//+:cnd:noEmit

namespace MyMod;

public static class BuildInfo
{
    public const string Name = "MyMod";
    public const string Description = "does stuff i guess";
    public const string Author = "me";
    public const string Version = "1.0.0";
}

public class MyMod : MelonMod
{
    private static MelonLogger.Instance Logger;

    public override void OnInitializeMelon()
    {
        Logger = LoggerInstance;
        Logger.Msg("MyMod initialized");
    }

    public override void OnSceneWasLoaded(int buildIndex, string sceneName)
    {
        Logger.Debug($"Scene loaded: {sceneName}");
        if (sceneName == "Main")
        {
            Logger.Debug("Main scene loaded, waiting for player");
            MelonCoroutines.Start(Utils.WaitForPlayer(DoStuff()));
        }
    }

    private IEnumerator DoStuff()
    {
        Logger.Msg("Player ready, doing stuff...");
        yield return new WaitForSeconds(2f);
        Logger.Msg("Did some stuff!");
    }
}

using MelonLoader;

[assembly:
    MelonInfo(typeof(MyMod.MyMod), MyMod.BuildInfo.Name,
        MyMod.BuildInfo.Version,
        MyMod.BuildInfo.Author)]
[assembly: MelonColor(1, 255, 255, 255)]
[assembly: MelonGame("TVGS", "Schedule I")]

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
    private static MelonLogger.Instance _logger;

    public override void OnInitializeMelon()
    {
        _logger = LoggerInstance;
        _logger.Msg("MyMod initialized");
        _logger.Debug("This will only show in debug mode");
    }
}
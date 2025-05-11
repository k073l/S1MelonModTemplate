using System.Diagnostics;
using MelonLoader;

namespace MyMod.Helpers;

public static class MelonLoggerExtensions
{
    public static void Debug(this MelonLogger.Instance logger, string message, bool stacktrace = true)
    {
#if RELEASE
        // if the build is in release mode, do not log debug messages
#else
        if (stacktrace)
        {
            var caller = GetCallerInfo();
            logger.Msg($"[DEBUG] {caller} - {message}");
        }
        else
            logger.Msg($"[DEBUG] {message}");
#endif
    }

    private static string GetCallerInfo()
    {
        var stackTrace = new StackTrace();
        for (int i = 2; i < stackTrace.FrameCount; i++)
        {
            var frame = stackTrace.GetFrame(i);
            var method = frame.GetMethod();
            if (method?.DeclaringType == null)
                continue;

            return $"{method.DeclaringType.FullName}.{method.Name}";
        }

        return "unknown";
    }
}
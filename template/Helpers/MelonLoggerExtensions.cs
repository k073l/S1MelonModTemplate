using System.Diagnostics;
using MelonLoader;

namespace MyMod.Helpers;

//-:cnd:noEmit
public static class MelonLoggerExtensions
{
    /// <summary>
    /// Logs a debug message to the console.
    /// Can provide caller info, otherwise it's just a convenience method to MelonDebug.
    /// This method only works when running with --melonloader.debug
    /// </summary>
    /// <param name="logger">Logger instance, isn't used.</param>
    /// <param name="message">The message to log.</param>
    /// <param name="stacktrace">Whether to include the stack trace in the log message. Defaults to true.</param>
    public static void Debug(
        this MelonLogger.Instance logger,
        string message,
        bool stacktrace = true
    )
    {
        MelonDebug.Msg(stacktrace ? $"[{GetCallerInfo()}] {message}" : message);
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

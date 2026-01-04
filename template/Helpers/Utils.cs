#nullable enable
using System.Collections;
using MelonLoader;
using UnityEngine;
using Color = UnityEngine.Color;

//-:cnd:noEmit
#if MONO
using ScheduleOne;
using ScheduleOne.DevUtilities;
using ScheduleOne.ItemFramework;
using ScheduleOne.PlayerScripts;
using FishNet;
#else
using Il2CppInterop.Runtime;
using Il2CppScheduleOne;
using Il2CppScheduleOne.DevUtilities;
using Il2CppScheduleOne.ItemFramework;
using Il2CppScheduleOne.PlayerScripts;
using Il2CppFishNet;
using Object = Il2CppSystem.Object;
#endif

//+:cnd:noEmit
namespace MyMod.Helpers;

//-:cnd:noEmit

/// <summary>
/// Provides extension methods for converting between C# and Il2Cpp lists.
/// </summary>
public static class Il2CppListExtensions
{
    /// <summary>
    /// Converts a C# <see cref="List{T}"/> to an <see cref="IEnumerable{T}"/>.
    /// It's a no-op for C# lists. Nonetheless, it is useful for Il2Cpp lists and it is recommended to use this method for consistency.
    /// </summary>
    /// <typeparam name="T">The type of the objects in the collection.</typeparam>
    /// <param name="source">The source enumerable to convert.</param>
    /// <returns>A C# <see cref="List{T}"/> containing the elements of the source.</returns>
    public static IEnumerable<T> AsEnumerable<T>(this List<T> list)
    {
        return list ?? [];
    }

    /// <summary>
    /// Converts the provided list to a backend-native list.
    /// On Il2Cpp, returns an Il2CppSystem.Collections.Generic.List{T}.
    /// On Mono, returns a System.Collections.Generic.List{T}.
    /// </summary>
    /// <typeparam name="T">The type of the objects in the collection.</typeparam>
    /// <param name="source">The source list to convert.</param>
    /// <returns>A backend-native list containing the elements of the source.</returns>
    public static object ToNativeList<T>(this List<T> source)
    {
#if !MONO
        return source.ToIl2CppList();
#else
        return source ?? new List<T>(); // already native
#endif
    }

#if !MONO
    /// <summary>
    /// Converts an <see cref="IEnumerable{T}"/> to an Il2Cpp <see cref="Il2CppSystem.Collections.Generic.List{T}"/>.
    /// </summary>
    /// <typeparam name="T">The type of the objects in the collection.</typeparam>
    /// <param name="source">The source enumerable to convert.</param>
    /// <returns>An Il2Cpp <see cref="Il2CppSystem.Collections.Generic.List{T}"/> containing the elements of the source.</returns>
    public static Il2CppSystem.Collections.Generic.List<T> ToIl2CppList<T>(
        this IEnumerable<T> source
    )
    {
        var il2CppList = new Il2CppSystem.Collections.Generic.List<T>();
        foreach (var item in source)
            il2CppList.Add(item);
        return il2CppList;
    }

    /// <summary>
    /// Converts an Il2Cpp <see cref="Il2CppSystem.Collections.Generic.List{T}"/> to a C# <see cref="List{T}"/>.
    /// </summary>
    /// <typeparam name="T">The type of the objects in the list.</typeparam>
    /// <param name="il2CppList">The Il2Cpp list to convert.</param>
    /// <returns>A C# <see cref="List{T}"/> containing the elements from the Il2Cpp list.</returns>
    public static List<T> ConvertToList<T>(Il2CppSystem.Collections.Generic.List<T> il2CppList)
    {
        List<T> csharpList = new List<T>();
        T[] array = il2CppList.ToArray();
        csharpList.AddRange(array);
        return csharpList;
    }

    /// <summary>
    /// Converts an Il2Cpp <see cref="Il2CppSystem.Collections.Generic.List{T}"/> to a C# <see cref="IEnumerable{T}"/>.
    /// </summary>
    /// <typeparam name="T">The type of the objects in the list.</typeparam>
    /// <param name="list">The Il2Cpp list to convert.</param>
    /// <returns>A C# <see cref="IEnumerable{T}"/> containing the elements from the Il2Cpp list.</returns>
    public static IEnumerable<T> AsEnumerable<T>(this Il2CppSystem.Collections.Generic.List<T> list)
    {
        return list == null ? [] : list._items.Take(list._size);
    }

    /// <summary>
    /// Converts the provided Il2Cpp list to a backend-native list.
    /// On Il2Cpp, returns an Il2CppSystem.Collections.Generic.List{T}.
    /// On Mono, this method is not available.
    /// </summary>
    /// <typeparam name="T">The type of the objects in the collection.</typeparam>
    /// <param name="source">The source Il2Cpp list to convert.</param>
    /// <returns>A backend-native list containing the elements of the source.</returns>
    public static object ToNativeList<T>(this Il2CppSystem.Collections.Generic.List<T> source)
    {
        return source; // already native
    }
#endif
}

/// <summary>
/// Common utility functions for the mod.
/// </summary>
public static class Utils
{
    private static readonly MelonLogger.Instance Logger = new MelonLogger.Instance(
        $"{BuildInfo.Name}-Utils"
    );

    /// <summary>
    /// Searches all loaded objects of type <typeparamref name="T"/> and returns the first one matching the given name.
    /// </summary>
    /// <typeparam name="T">The type of UnityEngine.Object to search for (e.g., Sprite, AudioClip).</typeparam>
    /// <param name="objectName">The name of the object to find.</param>
    /// <returns>The first matching object of type <typeparamref name="T"/> if found; otherwise, null.</returns>
    /// <example>
    /// <code>
    /// // Example usage for finding a Sprite by name
    /// var sprite = FindObjectByName&lt;‌Sprite‌&gt;("Dan_Mugshot");
    /// </code>
    /// </example>
    public static T? FindObjectByName<T>(string objectName)
        where T : UnityEngine.Object
    {
        try
        {
            foreach (var obj in Resources.FindObjectsOfTypeAll<T>())
            {
                if (obj.name != objectName)
                    continue;
                Logger.Debug($"Found {typeof(T).Name} '{objectName}' directly in loaded objects");
                return obj;
            }

            return null;
        }
        catch (Exception ex)
        {
            Logger.Error($"Error finding {typeof(T).Name} '{objectName}': {ex.Message}");
            return null;
        }
    }

    /// <summary>
    /// Gets all components of type <typeparamref name="T"/> in the given GameObject and its children recursively.
    /// </summary>
    /// <param name="obj">The GameObject to search in.</param>
    /// <typeparam name="T">The type of component to search for.</typeparam>
    /// <returns>A list of all components of type <typeparamref name="T"/> found in the GameObject and its children.</returns>
    /// <example>
    /// <code>
    /// // Example usage for getting all colliders in a GameObject
    /// List&lt;‌Collider‌&gt; colliders = GetAllComponentsInChildrenRecursive&lt;‌Collider‌&gt;(someGameObject);
    /// </code>
    /// </example>
    public static List<T> GetAllComponentsInChildrenRecursive<T>(GameObject obj)
        where T : Component
    {
        var results = new List<T>();
        if (obj == null)
            return results;

        T[] components = obj.GetComponents<T>();
        if (components.Length > 0)
        {
            results.AddRange(components);
        }

        for (var i = 0; i < obj.transform.childCount; i++)
        {
            var child = obj.transform.GetChild(i);
            results.AddRange(GetAllComponentsInChildrenRecursive<T>(child.gameObject));
        }

        return results;
    }

    /// <summary>
    /// Checks if the given object is of type <typeparamref name="T"/> and casts it to that type.
    /// </summary>
    /// <param name="obj">The object to check.</param>
    /// <param name="result">The cast object if the check is successful; otherwise, null.</param>
    /// <typeparam name="T">The type to check against.</typeparam>
    /// <returns>True if the object is of type <typeparamref name="T"/>; otherwise, false.</returns>
    /// <remarks>
    /// Method adapted from S1API (https://github.com/KaBooMa/S1API/blob/stable/S1API/Internal/Utils/CrossType.cs)
    /// </remarks>
    /// <example>
    /// <code>
    /// // Example usage for checking if an object is of type GameObject
    /// if (Is&lt;‌GameObject‌&gt;(someObject, out GameObject result))
    /// {
    ///     // Do something with result
    /// }
    /// </code>
    /// </example>
    public static bool Is<T>(object obj, out T? result)
#if !MONO
        where T : Object
#else
        where T : class
#endif
    {
#if !MONO
        if (obj is Object il2CppObj)
        {
            var targetType = Il2CppType.Of<T>();
            var objType = il2CppObj.GetIl2CppType();

            if (targetType.IsAssignableFrom(objType))
            {
                result = il2CppObj.TryCast<T>()!;
                return result != null;
            }
        }
#else
        if (obj is T t)
        {
            result = t;
            return true;
        }
#endif

        result = null;
        return false;
    }

    /// <summary>
    /// Waits for the player to be ready before starting the given coroutine.
    /// </summary>
    /// <param name="routine">Coroutine to start when player is ready</param>
    /// <returns>An enumerator that waits for the player to be ready.</returns>
    public static IEnumerator WaitForPlayer(IEnumerator routine)
    {
        while (Player.Local == null || Player.Local.gameObject == null)
            yield return null;

        // player is ready, start the coroutine
        MelonCoroutines.Start(routine);
    }

    /// <summary>
    /// Waits for the network to be ready before starting the given coroutine.
    /// </summary>
    /// <param name="routine">Coroutine to start when network is ready</param>
    /// <returns>An enumerator that waits for the network to be ready.</returns>
    public static IEnumerator WaitForNetwork(IEnumerator routine)
    {
        while (InstanceFinder.IsServer == false && InstanceFinder.IsClient == false)
            yield return null;
        // network is ready, start the coroutine
        MelonCoroutines.Start(routine);
    }

    /// <summary>
    /// Waits until the given condition is true, with optional timeout and callbacks.
    /// </summary>
    /// <param name="condition">The condition to wait for.</param>
    /// <param name="timeout">The maximum time to wait in seconds. If NaN, waits indefinitely.</param>
    /// <param name="onTimeout">Action to invoke if the timeout is reached.</param>
    /// <param name="onFinish">Action to invoke when the condition is met.</param>
    /// <returns>>An enumerator that waits for the condition to be true.</returns>
    public static IEnumerator WaitForCondition(
        System.Func<bool> condition,
        float timeout = Single.NaN,
        Action? onTimeout = null,
        Action? onFinish = null
    )
    {
        var startTime = Time.time;

        while (!condition())
        {
            if (!float.IsNaN(timeout) && Time.time - startTime > timeout)
            {
                onTimeout?.Invoke();
                yield break;
            }

            yield return null;
        }
        onFinish?.Invoke();
    }

    /// <summary>
    /// Gets the full hierarchy path of a Transform.
    /// </summary>
    /// <param name="transform">The Transform to get the path for.</param>
    /// <returns>The full hierarchy path.</returns>
    public static string GetHierarchyPath(this Transform transform)
    {
        if (transform == null) return "null";

        var path = transform.name;
        var current = transform.parent;

        while (current != null)
        {
            path = current.name + "/" + path;
            current = current.parent;
        }

        return path;
    }

    /// <summary>
    /// Gets a component or adds it if it doesn't exist.
    /// </summary>
    /// <typeparam name="T">The type of component.</typeparam>
    /// <param name="gameObject">The GameObject to get or add the component to.</param>
    /// <returns>The existing component or a newly added one.</returns>
    public static T GetOrAddComponent<T>(this GameObject gameObject) where T : Component
    {
        var component = gameObject.GetComponent<T>();
        if (component != null) return component;
        component = gameObject.AddComponent<T>();
        Logger.Debug($"Added component {typeof(T).Name} to GameObject {gameObject.name}");
        return component;
    }

    /// <summary>
    /// Draws debug visuals on the given GameObject by replacing its material with a transparent colored one.
    /// </summary>
    /// <param name="gameObject">The GameObject to draw debug visuals on.</param>
    /// <param name="color">The color to use for the debug visuals.</param>
    /// <returns>The original material of the GameObject's renderer.</returns>
    public static Material? DrawDebugVisuals(this GameObject gameObject, Color? color = null)
    {
        var renderer = gameObject.GetComponent<Renderer>();
        if (renderer == null)
        {
            Logger.Error($"GameObject {gameObject.name} has no Renderer component");
            return null;
        }

        color ??= new Color(1f, 0f, 1f, 0.5f);

        var shader = Shader.Find("Universal Render Pipeline/Lit");
        if (shader == null)
            return null;

        var mat = new Material(shader);

        if (mat.HasProperty("_Surface"))
            mat.SetFloat("_Surface", 1f);

        var baseColor = color.Value;
        if (baseColor.a <= 0f)
            baseColor.a = 0.2f;

        if (mat.HasProperty("_BaseColor"))
            mat.SetColor("_BaseColor", baseColor);

        if (mat.HasProperty("_EmissionColor"))
        {
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", new Color(baseColor.r, baseColor.g, baseColor.b) * 1.5f);
        }

        mat.SetInt("_ZWrite", 0);
        mat.renderQueue = 3000;

        var originalMaterial = renderer.material;
        renderer.material = mat;
        return originalMaterial;
    }
}

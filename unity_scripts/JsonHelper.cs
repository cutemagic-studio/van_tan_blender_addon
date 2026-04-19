using System;
using UnityEngine;

public static class JsonHelper
{

    public static T[] FromJson<T>(string json)
    {
        if (string.IsNullOrEmpty(json))
        {
            Debug.LogError("JSON is empty!");
            return new T[0];
        }

        // Bọc mảng lại để JsonUtility có thể đọc được
        string newJson = "{\"Items\":" + json + "}";

        Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(newJson);

        // Kiểm tra lỗi Parse (Cập nhật của bạn)
        if (wrapper == null || wrapper.Items == null)
        {
            Debug.LogError("JSON parse failed! Hãy kiểm tra định dạng file .json của bạn.");
            return new T[0];
        }

        return wrapper.Items;
    }

    // Class bọc mảng (Phải có Serializable)
    [Serializable]
    private class Wrapper<T>
    {
        public T[] Items;
    }
}
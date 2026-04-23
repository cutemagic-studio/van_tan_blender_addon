using System.Collections.Generic;
using System.Linq;

using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
#endif

[System.Serializable]
public class Vector3Data
{
    public float x, y, z;
}

[System.Serializable]
public class PropertiesData
{
    public int CMC_Id;
    public bool CMC_IsRootObject;
    public int CMC_RootObjectId;
    public string CMC_RootObjectName;
}

[System.Serializable]
public class PosData
{
    public string name;
    public Vector3Data pos;
    public PropertiesData properties; // Thuộc tính mới từ Blender
}

public class PositionImporter_2 : MonoBehaviour
{
    public TextAsset jsonFile;

    [Header("Prefab Library")]
    public List<GameObject> prefabLibrary; // Kéo các bản gốc từ Library vào đây

    [ContextMenu("Spawn Prefabs từ JSON")]
    public void SpawnPrefabsFromJSON()
    {
        if (jsonFile == null)
        {
            Debug.LogError("Thiếu JSON file!");
            return;
        }

        // Parse JSON thành mảng
        PosData[] allData = JsonHelper.FromJson<PosData>(jsonFile.text);

        if (allData == null || allData.Length == 0)
        {
            Debug.LogError("JSON rỗng hoặc parse lỗi!");
            return;
        }

        // Tạo một Dictionary để tìm Prefab nhanh hơn thay vì duyệt List liên tục
        Dictionary<string, GameObject> prefabMap = prefabLibrary
            .Where(p => p != null)
            .ToDictionary(p => p.name, p => p);

        int spawnCount = 0;

        foreach (var item in allData)
        {
            // BỎ QUA nếu object này là Root (vì Root chỉ nằm trong Library Scene của Blender)
            // Chúng ta chỉ spawn các Instance (IsRoot == false)
            //if (item.properties.CMC_IsRootObject) continue;

            // Sử dụng ?. để tránh crash nếu properties bị null
            string targetPrefabName = item.properties?.CMC_RootObjectName;

            // KIỂM TRA AN TOÀN: Nếu tên Prefab trống, bỏ qua để không gây lỗi crash
            if (string.IsNullOrEmpty(targetPrefabName))
            {
                Debug.LogWarning($"Bỏ qua object '{item.name}' vì dữ liệu rootName bị trống!");
                continue;
            }

            if (prefabMap.TryGetValue(targetPrefabName, out GameObject prefab))
            {
                // Tính toán vị trí
                Vector3 spawnPos = new Vector3(item.pos.x, item.pos.y, item.pos.z);

                // Spawn Prefab
                //GameObject newObj = Instantiate(prefab, spawnPos, Quaternion.identity);
                GameObject newObj;

                #if UNITY_EDITOR
                newObj = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
                newObj.transform.position = spawnPos;
                #else
                newObj = Instantiate(prefab, spawnPos, Quaternion.identity);
                #endif

                // Đặt tên và cho vào làm con của Object hiện tại để dễ quản lý
                newObj.name = $"{item.name}_Instance_{item.properties.CMC_Id}";
                //newObj.transform.SetParent(this.transform);

                spawnCount++;
            }
            else
            {
                Debug.LogWarning($"Không tìm thấy Prefab nào có tên: {targetPrefabName} trong Library!");
            }
        }

        Debug.Log($"✅ Đã Spawn thành công {spawnCount} objects vào Demo Scene!");
    }
}

// Helper để JsonUtility có thể đọc được Array
public static class JsonHelper
{
    public static T[] FromJson<T>(string json)
    {
        string newJson = "{ \"items\": " + json + " }";
        Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(newJson);
        return wrapper.items;
    }

    [System.Serializable]
    private class Wrapper<T>
    {
        public T[] items;
    }
}
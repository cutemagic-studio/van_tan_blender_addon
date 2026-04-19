using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class PosData
{
    public string name;
    public Vector3Data pos;
}

[System.Serializable]
public class Vector3Data
{
    public float x, y, z;
}

public class PositionImporter : MonoBehaviour
{
    public TextAsset jsonFile;

    [ContextMenu("Áp đặt vị trí cho Object có sẵn")]
    public void ApplyPositionsToExistingObjects()
    {
        if (jsonFile == null)
        {
            Debug.LogError("Thiếu JSON file!");
            return;
        }

        PosData[] allData = JsonHelper.FromJson<PosData>(jsonFile.text);

        if (allData == null || allData.Length == 0)
        {
            Debug.LogError("JSON rỗng hoặc parse lỗi!");
            return;
        }

        var allTransforms = GameObject.FindObjectsOfType<Transform>(true);
        Dictionary<string, Transform> map = new Dictionary<string, Transform>();

        foreach (var t in allTransforms)
            map[t.name] = t;

        int count = 0;

        foreach (var item in allData)
        {
            if (map.TryGetValue(item.name, out Transform target))
            {
                target.position = new Vector3(item.pos.x, item.pos.y, item.pos.z);
                count++;
            }
            else
            {
                Debug.LogWarning($"Không tìm thấy: {item.name}");
            }
        }

        Debug.Log($"Updated {count} objects!");
    }
}
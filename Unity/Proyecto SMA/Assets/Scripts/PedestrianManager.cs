using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class PedestrianManager : MonoBehaviour
{
    public GameObject pedestrianPrefab; // Prefab del peatón
    public string apiUrl = "http://127.0.0.1:5003/getPeaton"; // URL de la API

    private Dictionary<string, GameObject> pedestrians = new Dictionary<string, GameObject>(); // Rastrea peatones en la escena
    private HashSet<Vector2Int> validPositions = new HashSet<Vector2Int>(); // Posiciones válidas desde el JSON

    void Start()
    {
        StartCoroutine(UpdatePedestrians());
    }

    IEnumerator UpdatePedestrians()
    {
        while (true)
        {
            UnityWebRequest request = UnityWebRequest.Get(apiUrl);
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string json = request.downloadHandler.text;
                ProcessPedestrianData(json);
            }
            else
            {
                Debug.LogError($"Error al obtener datos de peatones: {request.error}");
            }

            yield return new WaitForSeconds(1); // Actualiza cada segundo
        }
    }

    private void ProcessPedestrianData(string json)
    {
        PedestrianData[] pedestrianDataArray = JsonUtility.FromJson<PedestrianWrapper>($"{{\"items\": {json}}}").items;

        validPositions.Clear(); // Limpia las posiciones válidas antes de procesar
        foreach (var pedestrianData in pedestrianDataArray)
        {
            validPositions.Add(new Vector2Int(pedestrianData.position[0], pedestrianData.position[1]));

            if (pedestrians.ContainsKey(pedestrianData.id))
            {
                UpdatePedestrianPosition(pedestrianData);
            }
            else
            {
                CreatePedestrian(pedestrianData);
            }
        }

        RemoveMissingPedestrians(pedestrianDataArray);
    }

    private void CreatePedestrian(PedestrianData pedestrianData)
    {
        Vector3 position = ConvertToUnityPosition(pedestrianData.position);
        GameObject newPedestrian = Instantiate(pedestrianPrefab, position, Quaternion.identity);

        pedestrians.Add(pedestrianData.id, newPedestrian);
        Debug.Log($"Peatón creado: {pedestrianData.id} en posición {position}");
    }

    private void UpdatePedestrianPosition(PedestrianData pedestrianData)
    {
        if (pedestrians.TryGetValue(pedestrianData.id, out GameObject pedestrian))
        {
            Vector3 newPosition = ConvertToUnityPosition(pedestrianData.position);
            pedestrian.transform.position = Vector3.Lerp(pedestrian.transform.position, newPosition, Time.deltaTime * 2f); // Movimiento suave
        }
    }

    private void RemoveMissingPedestrians(PedestrianData[] pedestrianDataArray)
    {
        HashSet<string> currentIds = new HashSet<string>();
        foreach (var pedestrianData in pedestrianDataArray)
        {
            currentIds.Add(pedestrianData.id);
        }

        List<string> idsToRemove = new List<string>();
        foreach (var id in pedestrians.Keys)
        {
            if (!currentIds.Contains(id))
            {
                idsToRemove.Add(id);
            }
        }

        foreach (var id in idsToRemove)
        {
            Destroy(pedestrians[id]);
            pedestrians.Remove(id);
            Debug.Log($"Peatón eliminado: {id}");
        }
    }

    private Vector3 ConvertToUnityPosition(int[] jsonPosition)
    {
        return new Vector3(jsonPosition[0], 0, jsonPosition[1]); // X -> X, Y -> Z
    }

    [System.Serializable]
    private class PedestrianWrapper
    {
        public PedestrianData[] items;
    }

    [System.Serializable]
    private class PedestrianData
    {
        public string id;
        public string color;
        public int[] position;
    }
}

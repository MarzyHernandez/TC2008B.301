using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class PedestrianManager : MonoBehaviour
{
    public GameObject pedestrianPrefab; // Prefab del peatón
    public string apiUrl = "http://127.0.0.1:5003/getPeatonEscalado"; // URL de la API
    //private float moveSpeed = 2f; // Velocidad de movimiento

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
            yield return new WaitForSeconds(0.1f); // Actualiza cada segundo
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
            Vector3 currentPosition = pedestrian.transform.position;
            Vector3 newPosition = ConvertToUnityPosition(pedestrianData.position);

            // Calcular dirección de movimiento
            Vector3 direction = (newPosition - currentPosition).normalized;

            // Calcular ángulo en el rango de -90° a 90°
            float targetAngle = Mathf.Atan2(direction.x, direction.z) * Mathf.Rad2Deg;
            targetAngle = Mathf.Clamp(targetAngle, -180f, 180f);

            // Aplicar rotación suavemente
            Quaternion targetRotation = Quaternion.Euler(0, targetAngle, 0);
            pedestrian.transform.rotation = Quaternion.Lerp(pedestrian.transform.rotation, targetRotation, Time.deltaTime * 10f);

            // Mover posición suavemente
            pedestrian.transform.position = Vector3.Lerp(currentPosition, newPosition, Time.deltaTime * 40f);
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
        return new Vector3(jsonPosition[0], 0, jsonPosition[1]); // Cambia a Y -> Z
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

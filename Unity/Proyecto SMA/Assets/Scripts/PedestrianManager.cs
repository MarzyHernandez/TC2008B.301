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

    private Dictionary<string, float> pedestrianTransitionTimers = new Dictionary<string, float>();
    private Dictionary<string, Vector3> pedestrianPositions = new Dictionary<string, Vector3>();

    private void UpdatePedestrianPosition(PedestrianData pedestrianData)
    {
        if (pedestrians.TryGetValue(pedestrianData.id, out GameObject pedestrian))
        {
            // Obtener la posición actual
            Vector3 currentPosition = pedestrianPositions.ContainsKey(pedestrianData.id)
                ? pedestrianPositions[pedestrianData.id]
                : pedestrian.transform.position;

            // Posición objetivo
            Vector3 newPosition = ConvertToUnityPosition(pedestrianData.position);

            // Si la posición actual está cerca de la posición objetivo, finaliza el movimiento
            if (Vector3.Distance(currentPosition, newPosition) < 0.01f)
            {
                pedestrianPositions[pedestrianData.id] = newPosition;
                pedestrian.transform.position = newPosition;
                return;
            }

            // Velocidad de movimiento
            float moveSpeed = 60f; // Ajusta según la velocidad deseada

            // Calcular dirección y desplazamiento
            Vector3 direction = (newPosition - currentPosition).normalized;
            Vector3 displacement = direction * moveSpeed * Time.deltaTime;

            // Asegurarse de no pasar la posición objetivo
            Vector3 updatedPosition = currentPosition + displacement;
            if (Vector3.Distance(updatedPosition, newPosition) > Vector3.Distance(currentPosition, newPosition))
            {
                updatedPosition = newPosition;
            }

            // Actualizar posición
            pedestrianPositions[pedestrianData.id] = updatedPosition;
            pedestrian.transform.position = updatedPosition; // Mover el peatón

            // Calcular el ángulo manualmente
            float angle = Mathf.Atan2(direction.z, direction.x) * Mathf.Rad2Deg;

            // Aplicar rotación manual a los vértices de la malla
            ApplyRotationToMesh(pedestrian, angle);

            // Depuración
            Debug.Log($"Peatón {pedestrianData.id}: Movido de {currentPosition} a {updatedPosition} hacia {newPosition}");
        }
    }


    private void ApplyPositionToMesh(GameObject pedestrian, Vector3 position)
    {
        MeshFilter meshFilter = pedestrian.GetComponent<MeshFilter>();
        if (meshFilter != null && meshFilter.mesh != null)
        {
            Mesh mesh = meshFilter.mesh;
            Vector3[] vertices = mesh.vertices;

            // Obtener el id del peatón
            string pedestrianId = null;
            foreach (var pair in pedestrians)
            {
                if (pair.Value == pedestrian)
                {
                    pedestrianId = pair.Key;
                    break;
                }
            }

            if (pedestrianId == null || !pedestrianPositions.ContainsKey(pedestrianId))
            {
                Debug.LogError($"No se pudo encontrar la posición actual para el peatón: {pedestrian.name}");
                return;
            }

            // Calcular desplazamiento
            Vector3 offset = position - pedestrianPositions[pedestrianId];

            // Aplicar desplazamiento a los vértices
            for (int i = 0; i < vertices.Length; i++)
            {
                vertices[i] += offset;
            }

            mesh.vertices = vertices;
            mesh.RecalculateBounds();
        }
    }

    private void ApplyRotationToMesh(GameObject pedestrian, float angle)
    {
        MeshFilter meshFilter = pedestrian.GetComponent<MeshFilter>();
        if (meshFilter != null && meshFilter.mesh != null)
        {
            Mesh mesh = meshFilter.mesh;
            Vector3[] vertices = mesh.vertices;

            // Convertir el ángulo a radianes
            float radians = angle * Mathf.Deg2Rad;

            // Crear la matriz de rotación
            float cos = Mathf.Cos(radians);
            float sin = Mathf.Sin(radians);

            // Rotar cada vértice alrededor del eje Y
            for (int i = 0; i < vertices.Length; i++)
            {
                float x = vertices[i].x;
                float z = vertices[i].z;

                vertices[i].x = cos * x - sin * z;
                vertices[i].z = sin * x + cos * z;
            }

            mesh.vertices = vertices;
            mesh.RecalculateBounds();
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

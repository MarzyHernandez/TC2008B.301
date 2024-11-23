using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class TrafficLightManager : MonoBehaviour
{
    public TrafficLightController[] trafficLights; // Referencias a los semáforos en Unity
    public string apiUrl = "http://127.0.0.1:5003/getLights"; // URL del API para obtener los estados de los semáforos

    void Start()
    {
        StartCoroutine(SynchronizeTrafficLights());
    }

    IEnumerator SynchronizeTrafficLights()
    {
        while (true)
        {
            UnityWebRequest request = UnityWebRequest.Get(apiUrl);
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string json = request.downloadHandler.text;
                ProcessTrafficLightData(json);
            }
            else
            {
                Debug.LogError($"Error al obtener datos del API: {request.error}");
            }

            // Actualiza los datos cada segundo
            yield return new WaitForSeconds(1);
        }
    }

    private void ProcessTrafficLightData(string json)
    {
        TrafficLightData trafficData = JsonUtility.FromJson<TrafficLightData>(json);

        foreach (var light in trafficLights)
        {
            foreach (var apiLight in trafficData.trafficLights)
            {
                // Compara IDs y actualiza el estado del semáforo correspondiente
                if (light.trafficLightId == apiLight.id)
                {
                    light.UpdateTrafficLightState(apiLight.color);
                }
            }
        }
    }
}

[System.Serializable]
public class TrafficLightData
{
    public TrafficLight[] trafficLights; // Lista de semáforos en el JSON
}

[System.Serializable]
public class TrafficLight
{
    public string id;       // ID del semáforo
    public Vector2 position; // Posición en el modelo 
    public string color;    // Estado del semáforo 
}

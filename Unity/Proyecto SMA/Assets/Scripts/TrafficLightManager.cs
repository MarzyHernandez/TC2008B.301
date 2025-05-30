using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class TrafficLightManager : MonoBehaviour
{
    public TrafficLightController[] trafficLights; // Lista de todos los semáforos en Unity
    public string apiUrl = "http://127.0.0.1:5003/getLights"; // URL de la API

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
                Debug.Log($"Datos recibidos del API: {json}");
                ProcessTrafficLightData(json);
            }
            else
            {
                Debug.LogError($"Error al obtener datos del API: {request.error}");
            }

            yield return new WaitForSeconds(0.1f); // Actualizar cada 0.7 segundos
        }
    }

/*    public bool CanVehiclePass(Vector2Int position)
    {
        foreach (var light in trafficLights)
        {
            foreach (var controlledPosition in light.controlledPositions)
            {
                if (controlledPosition == position && light.Red_Spot_Light.enabled)
                {
                    return false; // Detener el vehículo
                }
            }
        }
        return true; // Permitir el paso
    }*/


    private void ProcessTrafficLightData(string json)
    {
        TrafficLight[] trafficLightsData = JsonUtility.FromJson<TrafficLightWrapper>($"{{\"items\": {json}}}").items;

        foreach (var light in trafficLights)
        {
            foreach (var apiLight in trafficLightsData)
            {
                // Convierte la posición del JSON en Vector2Int
                Vector2Int apiPosition = new Vector2Int(apiLight.position[0], apiLight.position[1]);

                // Si la posición coincide, actualiza el estado
                if (light.controlledPosition == apiPosition)
                {
                    Debug.Log($"Actualizando semáforo en posición {light.controlledPosition} con estado {apiLight.color}");
                    light.UpdateTrafficLightState(apiLight.color);
                }
            }
        }
    }

    [System.Serializable]
    private class TrafficLightWrapper
    {
        public TrafficLight[] items;
    }
}

[System.Serializable]
public class TrafficLight
{
    public string id;         // ID del semáforo
    public string color;      // Estado del semáforo (green, yellow, red)
    public int[] position;    // Posición del semáforo en el mapa
}
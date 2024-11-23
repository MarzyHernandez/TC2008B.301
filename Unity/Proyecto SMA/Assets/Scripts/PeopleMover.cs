using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class PeopleMover : MonoBehaviour
{
    private const string API_URL = "http://127.0.0.1:5003/getPeatonEscalado";

    void Start()
    {
        StartCoroutine(FetchPedestrianData());
    }

    IEnumerator FetchPedestrianData()
    {
        while (true)
        {
            using (UnityWebRequest request = UnityWebRequest.Get(API_URL))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string jsonResponse = request.downloadHandler.text;

                    Debug.Log($"Datos recibidos del API: {jsonResponse}");
                }
                else
                {
                    Debug.LogError($"Error al obtener los datos del API: {request.error}");
                }
            }

            yield return new WaitForSeconds(2f); 
        }
    }
}

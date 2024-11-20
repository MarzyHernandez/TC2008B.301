using System.Collections;
using UnityEngine;
using UnityEngine.Networking; 

public class ModeloCarros : MonoBehaviour
{
    // URL del API (servidor local)
    private string apiUrl = "http://127.0.0.1:5003/getCarrosEscalado"; 

    void Start()
    {
        StartCoroutine(GetCarros());
    }

    IEnumerator GetCarros()
    {
        UnityWebRequest request = UnityWebRequest.Get(apiUrl);
        yield return request.SendWebRequest();

        if (request.isNetworkError || request.isHttpError)
        {
            Debug.LogError("Error: " + request.error);
        }
        else
        {
            string response = request.downloadHandler.text;
            Debug.Log("Respuesta de la API: " + response);

            ProcessCarrosData(response);
        }
    }

    void ProcessCarrosData(string jsonData)
    {
        // PROCESAR DATOS

        Carro[] carros = JsonHelper.FromJson<Carro>(jsonData);

        foreach (Carro carro in carros)
        {
            //  PARA CADA CARRO

            Debug.Log("Carro ID: " + carro.id + ", Posición: " + carro.position[0] + ", " + carro.position[1]);
        }
    }
}

[System.Serializable]
public class Carro
{
    public string id;
    public float[] position; 
}

public static class JsonHelper
{
    public static T[] FromJson<T>(string json)
    {
        string modifiedJson = "{\"items\":" + json + "}"; 
        Wrapper<T> wrapper = JsonUtility.FromJson<Wrapper<T>>(modifiedJson);
        return wrapper.items;
    }

    [System.Serializable]
    private class Wrapper<T>
    {
        public T[] items;
    }
}


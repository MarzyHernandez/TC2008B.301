using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking; // Para realizar peticiones HTTP

public class CarMover : MonoBehaviour
{
    public GameObject carPrefab; // Asigna el prefab del auto en el inspector
    private List<GameObject> cars = new List<GameObject>();
    private string endpointUrl = "http://127.0.0.1:5003/getCarrosEscalado"; // Cambia por tu endpoint
    private Dictionary<int, Vector3> carPositions = new Dictionary<int, Vector3>();

    private void Start()
    {
        StartCoroutine(UpdateCarDataPeriodically());
    }

    private IEnumerator UpdateCarDataPeriodically()
    {
        while (true)
        {
            yield return StartCoroutine(LoadCarData());
            yield return new WaitForSeconds(1f); // Llama a la API cada segundo
        }
    }

    private IEnumerator LoadCarData()
    {
        using (UnityWebRequest request = UnityWebRequest.Get(endpointUrl))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError($"Error fetching car data: {request.error}");
            }
            else
            {
                string jsonData = request.downloadHandler.text;
                UpdateCarPositions(jsonData);
            }
        }
    }

    private void UpdateCarPositions(string jsonData)
    {
        // Parsear el JSON a una lista de objetos
        List<CarData> carDataList = JsonUtility.FromJson<CarDataWrapper>($"{{\"cars\": {jsonData}}}").cars;

        foreach (CarData data in carDataList)
        {
            Vector3 newPosition = new Vector3(data.position[0], 0, data.position[1]);

            if (!carPositions.ContainsKey(data.id))
            {
                // Si es un auto nuevo, crearlo
                GameObject car = Instantiate(carPrefab, newPosition, Quaternion.identity);
                car.name = $"Car_{data.id}";
                cars.Add(car);
                carPositions[data.id] = newPosition;
            }
            else
            {
                // Actualizar posición del auto existente
                carPositions[data.id] = newPosition;
            }
        }
    }

    private void Update()
    {
        // Actualizar posiciones en cada frame
        foreach (GameObject car in cars)
        {
            int carId = int.Parse(car.name.Split('_')[1]);
            Vector3 target = carPositions[carId];
            Vector3 currentPosition = car.transform.position;
            Vector3 direction = (target - currentPosition).normalized;

            // Imprimir la posición actual y siguiente
            Debug.Log($"Car_{carId} - Current Position: {currentPosition} - Target Position: {target}");

            // Si hay una distancia significativa, mover y rotar el carro
            if (Vector3.Distance(currentPosition, target) > 0.1f)
            {
                StartCoroutine(RotateAndMoveCar(car, direction, target));
            }
        }
    }

    private IEnumerator RotateAndMoveCar(GameObject car, Vector3 direction, Vector3 target)
    {
        // Primero, rotamos el carro hacia la nueva dirección
        float rotationSpeed = 500f; // Velocidad de rotación
        Quaternion targetRotation = Quaternion.LookRotation(direction);
        
        // Rotamos el carro de manera rápida hacia la dirección deseada
        while (Quaternion.Angle(car.transform.rotation, targetRotation) > 1f)
        {
            car.transform.rotation = Quaternion.RotateTowards(car.transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
            yield return null;
        }

        // Luego, movemos el carro hacia la nueva posición
        float movementSpeed = 100f; // Velocidad de movimiento hacia la posición
        Vector3 currentPosition = car.transform.position;

        // Mover el carro hacia la nueva posición en 1 segundo
        while (Vector3.Distance(currentPosition, target) > 1f)
        {
            currentPosition = Vector3.MoveTowards(currentPosition, target, movementSpeed * Time.deltaTime);
            car.transform.position = currentPosition;
            yield return null;
        }

        // Asegurarse de que el carro llegue exactamente a la posición
        car.transform.position = target;
    }
}

// Clases para deserializar el JSON
[System.Serializable]
public class CarData
{
    public int id;
    public float[] position;
}

[System.Serializable]
public class CarDataWrapper
{
    public List<CarData> cars;
}

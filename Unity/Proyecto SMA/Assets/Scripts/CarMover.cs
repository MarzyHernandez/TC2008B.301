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
        // Velocidad de rotación
        float rotationSpeed = 100f; // Rotar 360 grados por segundo
        Quaternion targetRotation = Quaternion.LookRotation(direction);

        // Rotamos el carro hacia la nueva dirección rápidamente (en un segundo)
        float rotationTime = 1f; // Tiempo para rotar
        float elapsedRotationTime = 0f;
        Quaternion startRotation = car.transform.rotation;

        while (elapsedRotationTime < rotationTime)
        {
            car.transform.rotation = Quaternion.RotateTowards(startRotation, targetRotation, rotationSpeed * Time.deltaTime);
            elapsedRotationTime += Time.deltaTime;
            yield return null;
        }

        // Aseguramos que la rotación finaliza correctamente
        car.transform.rotation = targetRotation;

        // Movimiento hacia la nueva posición en 1 segundo
        float movementTime = 1f; // Tiempo para mover
        float elapsedMoveTime = 0f;
        Vector3 startPosition = car.transform.position;

        while (elapsedMoveTime < movementTime)
        {
            car.transform.position = Vector3.Lerp(startPosition, target, elapsedMoveTime / movementTime);
            elapsedMoveTime += Time.deltaTime;
            yield return null;
        }

        // Aseguramos que el carro llegue exactamente a la nueva posición
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

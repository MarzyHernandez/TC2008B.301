using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class CarController : MonoBehaviour
{
    private const string API_URL = "http://127.0.0.1:5003/getCarrosEscalado";
    public List<GameObject> carPrefabs; // Prefab asignado desde el inspector
    private Dictionary<int, GameObject> cars = new Dictionary<int, GameObject>();
    private Dictionary<int, Queue<Vector3>> carPaths = new Dictionary<int, Queue<Vector3>>();
    private Dictionary<int, Vector3> carPositions = new Dictionary<int, Vector3>();
    private Dictionary<int, Quaternion> carRotations = new Dictionary<int, Quaternion>();

    private float moveSpeed = 20f;
    private float rotationSpeed = 200f; // Grados por segundo

    void Start()
    {
        StartCoroutine(UpdateCarPositions());
    }

    IEnumerator UpdateCarPositions()
    {
        while (true)
        {
            using (UnityWebRequest request = UnityWebRequest.Get(API_URL))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string jsonResponse = request.downloadHandler.text;

                    if (!string.IsNullOrEmpty(jsonResponse))
                    {
                        CarDataListWrapper carDataWrapper = JsonUtility.FromJson<CarDataListWrapper>($"{{\"cars\":{jsonResponse}}}");
                        foreach (var carData in carDataWrapper.cars)
                        {
                            Vector3 newPosition = new Vector3(carData.position[0], 0f, carData.position[1]);

                            if (!cars.ContainsKey(carData.id))
                            {
                                GameObject selectedPrefab = carPrefabs[Random.Range(0, carPrefabs.Count)];
                                GameObject newCar = Instantiate(selectedPrefab, newPosition, Quaternion.identity);

                                newCar.name = $"Car_{carData.id}";
                                cars.Add(carData.id, newCar);

                                carPositions[carData.id] = newPosition;
                                carRotations[carData.id] = Quaternion.identity;

                                Queue<Vector3> path = new Queue<Vector3>();
                                path.Enqueue(newPosition);
                                carPaths.Add(carData.id, path);

                                Debug.Log($"Carro {carData.id} inicializado en posición: {newPosition}");
                            }
                            else
                            {
                                carPaths[carData.id].Enqueue(newPosition);

                                while (carPaths[carData.id].Count > 4)
                                {
                                    carPaths[carData.id].Dequeue();
                                }

                                Debug.Log($"Carro {carData.id}: nueva posición añadida {newPosition}");
                            }
                        }
                    }
                }
                else
                {
                    Debug.LogError("Error fetching car positions: " + request.error);
                }
            }
            yield return new WaitForSeconds(0.5f); // Llamada al API cada 0.5 segundos
        }
    }

    void Update()
    {
        foreach (var carEntry in cars)
        {
            int carId = carEntry.Key;
            GameObject car = carEntry.Value;

            if (carPaths[carId].Count > 1)
            {
                Vector3 currentTarget = carPaths[carId].Peek();

                if (Vector3.Distance(carPositions[carId], currentTarget) > 0.1f)
                {
                    MoveCarTowards(carId, currentTarget);
                    car.transform.position = carPositions[carId]; // Actualiza la posición real del objeto en la escena
                    car.transform.rotation = carRotations[carId]; // Actualiza la rotación real del objeto en la escena
                }
                else
                {
                    carPaths[carId].Dequeue();
                    Debug.Log($"Carro {carId} alcanzó el punto: {currentTarget}");
                }
            }
        }
    }

    private void MoveCarTowards(int carId, Vector3 target)
    {
        Vector3 direction = (target - carPositions[carId]).normalized;
        Quaternion targetRotation = Quaternion.LookRotation(direction);

        carRotations[carId] = Quaternion.RotateTowards(carRotations[carId], targetRotation, rotationSpeed * Time.deltaTime);
        carPositions[carId] = Vector3.MoveTowards(carPositions[carId], target, moveSpeed * Time.deltaTime);
    }
}

[System.Serializable]
public class CarData
{
    public int id;
    public List<float> position;
}

[System.Serializable]
public class CarDataListWrapper
{
    public List<CarData> cars;
}

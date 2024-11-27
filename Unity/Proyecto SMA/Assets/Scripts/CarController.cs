using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class CarController : MonoBehaviour
{
    private const string API_URL = "http://127.0.0.1:5003/getCarrosEscalado";
    public GameObject carPrefab; // Prefab asignado desde el inspector
    private Dictionary<int, GameObject> cars = new Dictionary<int, GameObject>();
    private Dictionary<int, Queue<Vector3>> carPaths = new Dictionary<int, Queue<Vector3>>();

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
                                GameObject newCar = Instantiate(carPrefab, newPosition, Quaternion.identity);
                                newCar.name = $"Car_{carData.id}";
                                cars.Add(carData.id, newCar);

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

                if (Vector3.Distance(car.transform.position, currentTarget) > 0.1f)
                {
                    MoveCarTowards(car, currentTarget);
                }
                else
                {
                    carPaths[carId].Dequeue();
                    Debug.Log($"Carro {carId} alcanzó el punto: {currentTarget}");
                }
            }
        }
    }

    private void MoveCarTowards(GameObject car, Vector3 target)
    {
        Vector3 direction = (target - car.transform.position).normalized;
        Quaternion targetRotation = Quaternion.LookRotation(direction);

        car.transform.rotation = Quaternion.RotateTowards(car.transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
        car.transform.position = Vector3.MoveTowards(car.transform.position, target, moveSpeed * Time.deltaTime);
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

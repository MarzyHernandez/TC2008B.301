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
    private Dictionary<int, Matrix4x4> carTransforms = new Dictionary<int, Matrix4x4>(); // Transformaciones homogéneas

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

                                Matrix4x4 initialTransform = VecOps.TranslateM(newPosition);
                                carTransforms[carData.id] = initialTransform;

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

                // Usar una posición posterior para orientación si hay suficientes puntos
                Vector3? orientationTarget = GetOrientationTarget(carPaths[carId]);

                if (Vector3.Distance(carTransforms[carId].MultiplyPoint3x4(Vector3.zero), currentTarget) > 0.1f)
                {
                    MoveCarTowards(carId, currentTarget, orientationTarget);
                    ApplyTransform(carId, car); // Actualiza la posición y rotación reales del objeto en la escena
                }
                else
                {
                    carPaths[carId].Dequeue();
                    Debug.Log($"Carro {carId} alcanzó el punto: {currentTarget}");
                }
            }
        }
    }

    private void MoveCarTowards(int carId, Vector3 target, Vector3? orientationTarget)
    {
        Vector3 currentPos = carTransforms[carId].MultiplyPoint3x4(Vector3.zero);
        Vector3 direction = (target - currentPos).normalized;

        // Orientar hacia el objetivo de orientación si existe, de lo contrario, hacia el objetivo actual
        Vector3 lookAtDirection = orientationTarget.HasValue
            ? (orientationTarget.Value - currentPos).normalized
            : direction;

        Matrix4x4 translation = VecOps.TranslateM(Vector3.MoveTowards(currentPos, target, moveSpeed * Time.deltaTime));

        Vector3 forward = carTransforms[carId].MultiplyVector(Vector3.forward);
        Vector3 newForward = Vector3.RotateTowards(forward, lookAtDirection, Mathf.Deg2Rad * rotationSpeed * Time.deltaTime, 0f).normalized;

        Vector3 right = Vector3.Cross(Vector3.up, newForward).normalized;
        Vector3 up = Vector3.Cross(newForward, right);

        Matrix4x4 rotation = new Matrix4x4();
        rotation.SetColumn(0, new Vector4(right.x, right.y, right.z, 0));
        rotation.SetColumn(1, new Vector4(up.x, up.y, up.z, 0));
        rotation.SetColumn(2, new Vector4(newForward.x, newForward.y, newForward.z, 0));
        rotation.SetColumn(3, new Vector4(0, 0, 0, 1));

        carTransforms[carId] = translation * rotation; // Combinación de traslación y rotación
    }

    private void ApplyTransform(int carId, GameObject car)
    {
        Matrix4x4 transform = carTransforms[carId];
        car.transform.localPosition = transform.MultiplyPoint3x4(Vector3.zero);

        Vector3 forward = transform.GetColumn(2);
        Vector3 up = transform.GetColumn(1);

        car.transform.localRotation = Quaternion.LookRotation(forward, up);
    }

    private Vector3? GetOrientationTarget(Queue<Vector3> path)
    {
        if (path.Count > 2)
        {
            Vector3[] points = path.ToArray();
            return points[2]; // Usar la tercera posición como objetivo de orientación
        }
        return null;
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

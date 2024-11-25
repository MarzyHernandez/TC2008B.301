using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class CarMover : MonoBehaviour
{
    private const string API_URL = "http://127.0.0.1:5003/getCarrosEscalado";
    public List<GameObject> carPrefabs; // Prefab asignado desde el inspector
    private Dictionary<int, GameObject> cars = new Dictionary<int, GameObject>();
    private bool isFirstCall = true;

    private float moveSpeed = 50f;
    private float rotationDuration = 0.3f; // Duración fija de la rotación en segundos

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
                        foreach (var car in carDataWrapper.cars)
                        {
                            Vector3 position = new Vector3(car.position[0], 0f, car.position[1]);

                            if (isFirstCall)
                            {
                                if (!cars.ContainsKey(car.id))
                                {
                                    GameObject newCar = InstantiateCar(car.id, position);
                                    cars.Add(car.id, newCar);
                                    Debug.Log($"Carro {car.id} inicializado en posición: {position}");
                                }
                            }
                            else
                            {
                                if (cars.ContainsKey(car.id))
                                {
                                    cars[car.id].GetComponent<CarController>().SetDestination(position);
                                    Debug.Log($"Carro {car.id} actualizado a nueva posición objetivo: {position}");
                                }
                            }
                        }

                        if (isFirstCall) isFirstCall = false;
                    }
                }
                else
                {
                    Debug.LogError("Error fetching car positions: " + request.error);
                }
            }

            yield return new WaitForSeconds(0.5f); // Llamada al API cada medio segundo
        }
    }

    private GameObject InstantiateCar(int id, Vector3 initialPosition)
    {
        // Seleccionar un prefab aleatorio de la lista
        GameObject selectedPrefab = carPrefabs[Random.Range(0, carPrefabs.Count)];

        // Crear una instancia del prefab seleccionado
        GameObject car = Instantiate(selectedPrefab, initialPosition, Quaternion.identity);
        car.name = "Car_" + id;

        CarController controller = car.AddComponent<CarController>();
        controller.Initialize(initialPosition, moveSpeed, rotationDuration);

        return car;
    }

}

public class CarController : MonoBehaviour
{
    private Vector3 currentPosition;
    private Vector3 destination;
    private Vector3 forwardDirection = Vector3.forward;
    private Vector3 targetDirection;
    private bool isRotating = false;

    private float moveSpeed;
    private float rotationDuration;
    private float rotationElapsed = 0f;

    public void Initialize(Vector3 initialPosition, float moveSpeed, float rotationDuration)
    {
        this.currentPosition = initialPosition;
        this.destination = initialPosition;
        this.moveSpeed = moveSpeed;
        this.rotationDuration = rotationDuration;

        // Coloca el prefab en la posición inicial
        ApplyTranslation(currentPosition);
    }

    public void SetDestination(Vector3 destination)
    {
        this.destination = destination;
        SetTargetRotation(currentPosition, destination);
        Debug.Log($"Carro {gameObject.name}: posición actual {currentPosition}, nueva posición objetivo {destination}");
    }

    void Update()
    {
        if (Vector3.Distance(currentPosition, destination) > 0.1f)
        {
            if (isRotating)
            {
                RotateTowards(targetDirection);
            }
            else
            {
                Vector3 direction = (destination - currentPosition).normalized;
                currentPosition += direction * moveSpeed * Time.deltaTime;
                ApplyTranslation(currentPosition);
            }
        }
        else
        {
            Debug.Log($"Carro {gameObject.name}: alcanzó su destino en {destination}");
        }
    }

    private void SetTargetRotation(Vector3 current, Vector3 next)
    {
        Vector3 direction = (next - current).normalized;
        targetDirection = direction;
        isRotating = true;
        rotationElapsed = 0f; // Reiniciar el tiempo de rotación
    }

    private void RotateTowards(Vector3 direction)
    {
        rotationElapsed += Time.deltaTime;
        float rotationStep = Mathf.Clamp01(rotationElapsed / rotationDuration);

        if (rotationStep >= 1f)
        {
            forwardDirection = direction;
            isRotating = false;
        }
        else
        {
            float angle = Vector3.SignedAngle(forwardDirection, direction, Vector3.up);
            float step = angle * rotationStep;
            Matrix4x4 rotationMatrix = VecOps.RotateYM(step);
            forwardDirection = rotationMatrix.MultiplyPoint3x4(forwardDirection).normalized;

            ApplyRotation(forwardDirection); // Aplicar la rotación
        }
    }

    private void ApplyTranslation(Vector3 position)
    {
        Matrix4x4 translationMatrix = VecOps.TranslateM(position);

        // Aplicar la traslación al prefab
        Vector3 transformedPosition = translationMatrix.MultiplyPoint3x4(Vector3.zero);
        Debug.Log($"{gameObject.name} movido a posición: {transformedPosition}");
        transform.localPosition = transformedPosition;
    }

    private void ApplyRotation(Vector3 forwardDirection)
    {
        Vector3 right = Vector3.Cross(Vector3.up, forwardDirection).normalized;
        Vector3 up = Vector3.Cross(forwardDirection, right);

        Matrix4x4 rotationMatrix = new Matrix4x4();
        rotationMatrix.SetColumn(0, new Vector4(right.x, right.y, right.z, 0));
        rotationMatrix.SetColumn(1, new Vector4(up.x, up.y, up.z, 0));
        rotationMatrix.SetColumn(2, new Vector4(forwardDirection.x, forwardDirection.y, forwardDirection.z, 0));
        rotationMatrix.SetColumn(3, new Vector4(0, 0, 0, 1));

        // Aplicar la rotación calculada al prefab
        transform.localRotation = MatrixToQuaternion(rotationMatrix);
    }

    private Quaternion MatrixToQuaternion(Matrix4x4 m)
    {
        float w = Mathf.Sqrt(1.0f + m.m00 + m.m11 + m.m22) / 2.0f;
        float w4 = (4.0f * w);
        float x = (m.m21 - m.m12) / w4;
        float y = (m.m02 - m.m20) / w4;
        float z = (m.m10 - m.m01) / w4;

        return new Quaternion(x, y, z, w);
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
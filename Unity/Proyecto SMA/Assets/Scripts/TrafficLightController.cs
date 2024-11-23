using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TrafficLightController : MonoBehaviour
{
    public Light Green_Spot_Light;
    public Light Yellow_Spot_Light;
    public Light Red_Spot_Light;
    public Light Green1_Spot_Light;
    public Light Red1_Spot_Light;
    public float vehicleGreenTime = 10f;
    public float vehicleYellowTime = 2f;
    public float vehicleRedTime = 12f;
    private float cycleTime;
    private float startTime;

    void Start()
    {
        cycleTime = vehicleGreenTime + vehicleYellowTime + vehicleRedTime;

        // Si el tiempo de inicio no se ha sincronizado, lo inicializamos al tiempo actual
        if (startTime == 0f)
        {
            startTime = Time.time;
        }

        StartCoroutine(SynchronizeTrafficLights());
    }

    IEnumerator SynchronizeTrafficLights()
    {
        while (true)
        {
            float elapsed = (Time.time - startTime) % cycleTime;

            if (elapsed < vehicleGreenTime)
            {
                SetTrafficLights(true, false, false, false, true); // Vehículos: verde, Peatones: rojo
            }
            else if (elapsed < vehicleGreenTime + vehicleYellowTime)
            {
                SetTrafficLights(false, true, false, false, true); // Vehículos: amarillo, Peatones: rojo
            }
            else
            {
                SetTrafficLights(false, false, true, true, false); // Vehículos: rojo, Peatones: verde
            }

            yield return null;
        }
    }

    public void SetStartTime(float globalStartTime)
    {
        startTime = globalStartTime;
    }

    private void SetTrafficLights(bool vehicleGreen, bool vehicleYellow, bool vehicleRed, bool pedestrianGreen, bool pedestrianRed)
    {
        Green_Spot_Light.enabled = vehicleGreen;
        Yellow_Spot_Light.enabled = vehicleYellow;
        Red_Spot_Light.enabled = vehicleRed;

        Green1_Spot_Light.enabled = pedestrianGreen;
        Red1_Spot_Light.enabled = pedestrianRed;
    }
}

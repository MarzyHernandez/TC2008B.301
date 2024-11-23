using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TrafficLightController : MonoBehaviour
{
    // Luces de vehículo
    public Light Green_Spot_Light;
    public Light Yellow_Spot_Light;
    public Light Red_Spot_Light;

    // Luces de peatón
    public Light Green1_Spot_Light;
    public Light Red1_Spot_Light;

    // Posiciones controladas por este semáforo (pueden ser 1 o más)
    public Vector2Int[] controlledPositions;

    public void UpdateTrafficLightState(string state)
    {
        Debug.Log($"Cambiando estado del semáforo en {controlledPositions[0]} a {state}");

        switch (state.ToLower())
        {
            case "green":
                SetVehicleLightStates(true, false, false);
                SetPedestrianLightStates(false, true); // Peatón: rojo
                break;

            case "yellow":
                SetVehicleLightStates(false, true, false);
                SetPedestrianLightStates(false, true); // Peatón: rojo
                break;

            case "red":
                SetVehicleLightStates(false, false, true);
                SetPedestrianLightStates(true, false); // Peatón: verde
                break;

            default:
                Debug.LogWarning($"Estado desconocido para el semáforo en {controlledPositions[0]}: {state}");
                break;
        }
    }

    private void SetVehicleLightStates(bool green, bool yellow, bool red)
    {
        Green_Spot_Light.enabled = green;
        Yellow_Spot_Light.enabled = yellow;
        Red_Spot_Light.enabled = red;
    }

    private void SetPedestrianLightStates(bool green, bool red)
    {
        Green1_Spot_Light.enabled = green;
        Red1_Spot_Light.enabled = red;
    }
}

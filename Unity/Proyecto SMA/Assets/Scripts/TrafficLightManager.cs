using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TrafficLightManager : MonoBehaviour
{
    public TrafficLightController[] trafficLights;

    void Start()
    {
        float globalStartTime = Time.time;

        foreach (TrafficLightController light in trafficLights)
        {
            light.SetStartTime(globalStartTime);
        }
    }
}

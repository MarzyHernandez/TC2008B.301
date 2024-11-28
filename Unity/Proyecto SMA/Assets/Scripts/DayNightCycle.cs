using UnityEngine;

public class DayNightCycle : MonoBehaviour
{
    public Material skyboxDay; // Skybox para el día
    public Material skyboxEvening; // Skybox para el atardecer
    public Material skyboxNight; // Skybox para la noche
    public Light sunLight; // Luz direccional que simula el sol
    public Light[] cityLights; // Luces de la ciudad (Point Lights)

    public float cycleDuration = 30f; // Duración del ciclo en segundos
    private float time; // Contador del ciclo

    void Update()
    {
        // Incrementa el tiempo del ciclo
        time += Time.deltaTime;

        // Normaliza el tiempo en un ciclo (0 a 1)
        float normalizedTime = (time % cycleDuration) / cycleDuration;

        // Cambia el skybox y ajusta la luz solar
        if (normalizedTime < 0.33f) // Día
        {
            RenderSettings.skybox = skyboxDay;
            sunLight.intensity = Mathf.Lerp(0.8f, 1f, normalizedTime / 0.33f);

            ToggleCityLights(false);
        }
        else if (normalizedTime < 0.66f) // Atardecer
        {
            RenderSettings.skybox = skyboxEvening;
            sunLight.intensity = Mathf.Lerp(0.6f, 0.3f, (normalizedTime - 0.33f) / 0.33f);

            ToggleCityLights(false);
        }
        else // Noche
        {
            RenderSettings.skybox = skyboxNight;
            sunLight.intensity = Mathf.Lerp(0.1f, 0f, (normalizedTime - 0.66f) / 0.34f);

            ToggleCityLights(true);
        }

        // Aplica los cambios en tiempo real
        DynamicGI.UpdateEnvironment();
    }

    // Función para encender o apagar las luces de la ciudad
    void ToggleCityLights(bool state)
    {
        foreach (Light cityLight in cityLights)
        {
            cityLight.enabled = state;
        }
    }
}
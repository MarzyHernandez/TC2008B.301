using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class RUN : MonoBehaviour
{
    public float speed = 5f; // Movement speed
    private Animator animator;
    private Vector3 movement;

    void Start()
    {
        // Get the Animator component
        animator = GetComponent<Animator>();

        if (animator == null)
        {
            Debug.LogError("Animator component missing from this GameObject!");
        }
    }

    void Update()
    {
        HandleMovement();
        HandleAnimations();
    }

    private void HandleMovement()
    {
        // Get input for movement
        float moveX = Input.GetAxis("Horizontal");
        float moveZ = Input.GetAxis("Vertical");

        // Set movement vector
        movement = new Vector3(moveX, 0, moveZ).normalized;

        // Move the character
        if (movement.magnitude > 0)
        {
            transform.Translate(movement * speed * Time.deltaTime, Space.World);
            transform.rotation = Quaternion.LookRotation(movement);
        }
    }

    private void HandleAnimations()
    {
        // Set isWalking if there is movement
        bool isWalking = movement.magnitude > 0;
        animator.SetBool("isWalking", isWalking);

        // Trigger isDancing with the "D" key
        if (Input.GetKeyDown(KeyCode.D))
        {
            animator.SetBool("isDancing", true);
        }
        else if (Input.GetKeyUp(KeyCode.D))
        {
            animator.SetBool("isDancing", false);
        }

        // Disable walking animation if dancing
        if (animator.GetBool("isDancing"))
        {
            animator.SetBool("isWalking", false);
        }
    }
}

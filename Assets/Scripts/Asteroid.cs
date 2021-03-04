using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Asteroid : MonoBehaviour
{
    [SerializeField]
    private float orig_speed = 0.5f;
    private float speed;
    [SerializeField]
    private float wait_time = 0.5f;

    private Vector3 start_pos;
    private Vector3 start_scale;
    private MeshRenderer my_mesh_renderer;
    private SphereCollider my_col;

    // Start is called before the first frame update
    void Start()
    {
        start_pos = transform.position;
        start_scale = transform.localScale;
        my_mesh_renderer = GetComponent<MeshRenderer>();
        my_col = GetComponent<SphereCollider>();

        float speed_random = Random.Range(0.8f, 1.2f);
        speed = orig_speed * speed_random;

        StartCoroutine("Travel");
    }

    IEnumerator Travel()
    {
        float start_random = Random.Range(0.0f, 0.5f);
        yield return new WaitForSeconds(start_random);

        while (true)
        {
            // Setup
            my_mesh_renderer.enabled = true;
            my_col.enabled = true;
            transform.localScale = start_scale;
            transform.position = start_pos;
            transform.LookAt(Vector3.zero); // Point at origin

            // Main movement
            float radius = transform.position.sqrMagnitude;
            while (radius > 30.0f) // 25 is world radius, but want a little before
            {
                transform.Translate(Vector3.forward * 0.1f * speed);
                radius = transform.position.sqrMagnitude;
                yield return new WaitForFixedUpdate();
            }
            // Dissolve effect
            for (int _ = 0; _ < 20; _++)
            {
                transform.localScale *= 0.7f;
                transform.Translate(Vector3.forward * 0.1f);
                yield return new WaitForFixedUpdate();
            }
            transform.localScale = Vector3.zero;

            // Wrap up + wait time
            my_mesh_renderer.enabled = false;
            my_col.enabled = false;
            float wait_random = Random.Range(0.8f, 1.2f);
            for (int _ = 0; _ < 50.0f * wait_time * wait_random; _++)
            {
                yield return new WaitForFixedUpdate();
            }
            float speed_random = Random.Range(0.8f, 1.2f);
            speed = orig_speed * speed_random;
        }
    }
}

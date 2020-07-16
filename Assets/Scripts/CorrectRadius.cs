using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CorrectRadius : MonoBehaviour
{
    public float offset = 1.0f;

    // Start is called before the first frame update
    void Start()
    {
        GameObject world = GameObject.Find("World");
        float world_radius = world.transform.localScale.y / 2.0f;

        Quaternion orig_rot = transform.rotation;

        transform.LookAt(world.transform);

        Vector3 p = transform.position;// + (offset * transform.forward);

        float r = Mathf.Sqrt(Mathf.Pow(p.x, 2.0f) + Mathf.Pow(p.y, 2.0f) + Mathf.Pow(p.z, 2.0f));
        
        float dist = (r - world_radius) - offset;
        transform.Translate(Vector3.forward * dist, Space.Self);

        //Debug.Log("World radius: " + world_radius + " | My radius: " + r + " | Moved amount: " + dist + "(Offset " + offset + ")");

        transform.rotation = orig_rot;
    }
}

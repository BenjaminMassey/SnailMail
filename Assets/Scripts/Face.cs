using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Face : MonoBehaviour
{
    public GameObject Object_to_Face;

    void FixedUpdate()
    {
        transform.LookAt(Object_to_Face.transform);
    }
}

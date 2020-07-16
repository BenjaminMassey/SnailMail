using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class FaceCamera : MonoBehaviour
{

    private GameObject cam;

    private void Start()
    {
        cam = GameObject.Find("Main Camera");
    }

    void FixedUpdate()
    {
        transform.LookAt(cam.transform);
    }
}

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class LookAtCenter : MonoBehaviour
{
    [SerializeField]
    private Vector3 offset = Vector3.zero;

    // Start is called before the first frame update
    void Start()
    {
        transform.LookAt(Vector3.zero);
        transform.Rotate(offset);
    }
}

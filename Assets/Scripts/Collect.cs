using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Collect : MonoBehaviour
{
    public AudioSource DingSound;

    private void OnTriggerEnter(Collider other)
    {
        if (other.gameObject.tag.Equals("Collectable"))
        {
            DingSound.Play();
            Destroy(other.gameObject);
        }
    }
}

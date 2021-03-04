using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Kill : MonoBehaviour
{
    public AudioSource Puff;

    private void OnTriggerEnter(Collider other)
    {
        if (LevelEnd.level_completed) return;
        if (other.gameObject.name.Equals("Character"))
        {
            Puff.Play();
            Destroy(GameObject.Find("Snail"));
            //GameObject.Find("Snail").transform.GetChild(0).gameObject.GetComponent<MeshRenderer>().enabled = false; // I'm sorry
            other.gameObject.GetComponent<Move>().enabled = false;
            MessageHandler.Message("You died...", 1.0f);
            StartCoroutine("Restart");
        }
    }
    IEnumerator Restart()
    {
        yield return new WaitForSeconds(1.0f);
        Resetter.Reset();
    }
}

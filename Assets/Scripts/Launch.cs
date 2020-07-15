using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Launch : MonoBehaviour
{
    public AudioSource Boing;

    private bool doing = false;

    private Vector3 direction;

    private GameObject character;
    private Vector3 char_pos;
    private Vector3 my_pos;

    void Start()
    {
        character = GameObject.Find("Bottom");
    }

    private void Update()
    {
        char_pos = character.transform.position;
        my_pos = transform.position;
        
        if (/*Close(Mathf.Round(char_pos.x), Mathf.Round(my_pos.x)) &&
            Close(Mathf.Round(char_pos.y), Mathf.Round(my_pos.y)) &&
            Close(Mathf.Round(char_pos.z), Mathf.Round(my_pos.z))*/
            GetComponent<Collider>().bounds.Contains(char_pos))
        {
            Do();
        }
    }

    bool Close(float a, float b)
    {
        return Mathf.Abs(a - b) <= 0.985f;
    }

    private void Do()
    {
        Debug.Log("LAUNCH");
        if (name.Contains("Left"))
        {
            direction = Vector3.left;
        }
        else if (name.Contains("Down"))
        {
            direction = Vector3.back;
        }
        else if (name.Contains("Jump"))
        {
            direction = Vector3.up;
        }
        else
        {
            Debug.Log("Unknown Launch.cs container");
            Destroy(gameObject); // ABORT ABORT
        }
        Boing.Play();
        StartCoroutine("Send");
    }

    IEnumerator Send()
    {
        Debug.Log("Attempted Launch.Send(), doing: " + doing);
        if (!doing)
        {
            Debug.Log("ATTEMPTING A LAUNCH PASSED");
            doing = true;
            GameObject character = GameObject.Find("Character");
            int amount = 10;
            float x = 1.0f;
            if (direction.Equals(Vector3.up)) { amount = 30;  x = 0.6f; character.GetComponent<Move>().gravity_on = false; }
            for (int i = 0; i < amount; i++)
            {
                character.transform.Translate(direction * 0.4f * x);
                yield return new WaitForFixedUpdate();
            }
            doing = false;
            character.GetComponent<Move>().gravity_on = true;
            Destroy(gameObject);
        }
    }
}

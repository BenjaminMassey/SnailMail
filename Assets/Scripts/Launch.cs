﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Launch : MonoBehaviour
{
    public AudioSource Boing;

    private bool doing = false;

    private Vector3 direction;

    private GameObject character;
    private GameObject bottom;
    private Vector3 char_pos;
    private Vector3 bottom_pos;
    private Vector3 my_pos;
    private Collider col;

    void Start()
    {
        //character = GameObject.Find("Bottom");
        character = GameObject.Find("Character");
        bottom = GameObject.Find("Bottom");
    }

    private void Update()
    {
        char_pos = character.transform.position;
        bottom_pos = bottom.transform.position;
        my_pos = transform.position;

        col = GetComponent<Collider>();

        if (col.bounds.Contains(char_pos) ||
            col.bounds.Contains(bottom_pos))
        {
            Do();
        }
    }

    private void Do()
    {
        Debug.Log("LAUNCH");
        if (name.Contains("Left"))
        {
            direction = Vector3.left;
        }
        else if (name.Contains("Right"))
        {
            direction = Vector3.right;
        }
        else if (name.Contains("Up"))
        {
            direction = Vector3.forward;
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
            Move mover = character.GetComponent<Move>();
            /* This is probably better, but currently hard to work with, so not using
             * Snap player to pad pos in order to normalize positioning
            int frames = 3;
            Vector3 snap_step = (transform.position - character.transform.position) / frames;
            for (int i = 0; i < frames; i++)
            {
                character.transform.Translate(snap_step);
                yield return new WaitForFixedUpdate();
            }
            */
            int amount = 10;
            float x = 1.0f;
            if (direction.Equals(Vector3.up)) { amount = 30; x = 0.6f; mover.gravity_on = false; }
            else { mover.move_on = false; }
            for (int i = 0; i < amount; i++)
            {
                character.transform.Translate(direction * 0.4f * x);
                yield return new WaitForFixedUpdate();
            }
            doing = false;
            mover.move_on = true;
            character.GetComponent<Move>().gravity_on = true;
            Destroy(gameObject);
        }
    }
}

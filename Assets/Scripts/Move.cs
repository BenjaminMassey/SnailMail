using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Move : MonoBehaviour
{
    public float MoveSpeed = 5.0f;
    public float GravSpeed = 0.15f;

    public GameObject world;
    public Transform my_bottom;
    public GameObject snail_obj;

    public bool gravity_on;

    private float my_height;
    private float world_height;

    private Vector2 move_rotate;

    private bool facing_up;

    // Start is called before the first frame update
    void Start()
    {
        my_height = transform.localScale.y / 2.0f;
        world_height = world.transform.localScale.y / 2.0f;

        move_rotate = new Vector3(0.0f, 0.0f);

        facing_up = true;

        gravity_on = true;
    }

    // Update is called once per frame
    void Update()
    {
        HandleMove();
        Gravity();
    }

    void HandleMove()
    {
        float horInp = 0.0f;
        float verInp = 0.0f;
        /*
        if (Input.GetKey(KeyCode.Mouse0))
        {
            Vector3 mp = Input.mousePosition;
            Debug.Log("Touch at " + mp);
            if (mp.y > Screen.height / 2.0f)
            {
                verInp = 1.0f;
            }
            else
            {
                horInp = 1.0f;
            }
        }
        */
        if (Buttons.right_button) { horInp = 1.0f; }
        if (Buttons.up_button) { verInp = 1.0f; }

        if (horInp + verInp == 2.0f)
        {
            horInp *= 0.66f;
            verInp *= 0.66f;
        }

        Vector3 move = new Vector3(horInp, 0.0f, verInp);

        move *= Time.deltaTime * MoveSpeed;

        transform.Translate(move);

        if (horInp == 1.0f && facing_up)
        {
            snail_obj.transform.Rotate(0.0f, 0.0f, 90.0f);
            facing_up = false;
        }
        else if (horInp == 0.0f && !facing_up)
        {
            snail_obj.transform.Rotate(0.0f, 0.0f, -90.0f);
            facing_up = true;
        }
    }

    void Gravity()
    {

        transform.LookAt(world.transform);

        Vector3 p = my_bottom.transform.position;

        float r = Mathf.Sqrt(Mathf.Pow(p.x, 2.0f) + Mathf.Pow(p.y, 2.0f) + Mathf.Pow(p.z, 2.0f));
        
        if (r > world_height && gravity_on)
        {
            float dist = r - world_height;
            if (dist > GravSpeed * Time.deltaTime)
            {
                transform.Translate(Vector3.forward * GravSpeed * Time.deltaTime, Space.Self);
            }
            else
            {
                transform.Translate(Vector3.forward * dist, Space.Self);
            }
        }

        transform.Rotate(-90.0f, 0.0f, 0.0f);
    }
}

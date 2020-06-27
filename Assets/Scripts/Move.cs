using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Move : MonoBehaviour
{
    public GameObject world;
    public Transform my_bottom;
    public Transform world_top;
    public GameObject snail_obj;

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
    }

    // Update is called once per frame
    void Update()
    {
        //TestMove();
        
        transform.LookAt(world.transform);

        transform.Rotate(-90.0f, 0.0f, 0.0f);

        world.transform.LookAt(transform);

        world.transform.Rotate(90.0f, 0.0f, 0.0f);

        if (!my_bottom.position.ToString().Equals(world_top.position.ToString()))
        {
            float distance = Vector3.Distance(my_bottom.position, world_top.position);

            if (distance > 0.4f)
            {
                Vector3 p = my_bottom.position - world_top.position;
                float r = Mathf.Sqrt(Mathf.Pow(p.x, 2.0f) + Mathf.Pow(p.y, 2.0f) + Mathf.Pow(p.z, 2.0f));
                float direction;
                if (r < world_height) { direction = 1.0f; }
                else if (r > world_height) { direction = -1.0f; }
                else { direction = 0.0f; }
                
                transform.Translate(Vector3.up * distance * direction, Space.Self);
            }
        }

        HandleMove();
    }

    void HandleMove()
    {
        float horInp = 0.0f;
        if (Input.GetKey(KeyCode.Mouse0)) { horInp = 1.0f; }

        float verInp = 0.0f;
        if (Input.GetKey(KeyCode.Mouse1)) { verInp = 1.0f; }

        if (horInp + verInp == 2.0f)
        {
            horInp *= 0.66f;
            verInp *= 0.66f;
        }

        Vector3 move = new Vector3(horInp, 0.0f, verInp) * 0.1f;

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

    void TestMove()
    {
        float horInp = 0.0f;
        if (Input.GetKey(KeyCode.A)) { horInp += -1.0f; }
        if (Input.GetKey(KeyCode.D)) { horInp += 1.0f; }

        float verInp = 0.0f;
        if (Input.GetKey(KeyCode.S)) { verInp += -1.0f; }
        if (Input.GetKey(KeyCode.W)) { verInp += 1.0f; }

        if (Mathf.Abs(horInp) + Mathf.Abs(verInp) == 2.0f)
        {
            horInp *= 0.66f;
            verInp *= 0.66f;
        }

        Vector3 move = new Vector3(horInp, 0.0f, verInp) * 0.1f;

        transform.Translate(move);
    }
}

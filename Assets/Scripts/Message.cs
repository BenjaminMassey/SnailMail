using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class Message : MonoBehaviour
{
    public float time;
    public string message;

    private Text t;

    // Start is called before the first frame update
    void Start()
    {
        time = 1.0f;
        message = "";
        t = GetComponent<Text>();
    }

    // Update is called once per frame
    IEnumerator Send()
    {
        t.text = message;
        t.enabled = true;
        yield return new WaitForSeconds(time);
        t.text = "";
        t.enabled = false;
    }
}

public static class MessageHandler
{
    public static void Message(string message, float time)
    {
        Message m = GameObject.Find("Text").GetComponent<Message>();
        if (m != null)
        {
            m.message = message;
            m.time = time;
            m.StartCoroutine("Send");
        }
        else
        {
            Debug.Log("FAILED VERY HARD TO SEND MESSAGE");
        }
    }
}

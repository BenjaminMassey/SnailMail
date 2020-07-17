using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class End : MonoBehaviour
{
    public AudioSource Cheer;
    public AudioSource Aww;

    private float delay = 1.5f;

    private GameObject main_section;
    private GameObject results_section;
    private GameObject results_obj;

    private float start_time;

    // Start is called before the first frame update
    void Start()
    {
        main_section = GameObject.Find("MainSection");
        results_section = GameObject.Find("ResultsSection");
        results_obj = GameObject.Find("Results Info");

        main_section.transform.localScale = Vector3.one;
        results_section.transform.localScale = Vector3.zero;

        start_time = Time.realtimeSinceStartup;
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.gameObject.name.Equals("Character"))
        {
            int count = NumCollected();
            if (count == 0)
            {
                Cheer.Play();
                MessageHandler.Message("You delivered the mail!", delay);
                StartCoroutine("ShowResults");
            }
            else
            {
                Aww.Play();
                string message = "You missed " + count + " letter";
                if (count == 1) { message += "."; }
                else { message += "s.";  }
                MessageHandler.Message(message, delay);
                StartCoroutine("Restart");
            }
        }
    }

    IEnumerator Restart()
    {
        GameObject.Find("Character").GetComponent<Move>().enabled = false;
        yield return new WaitForSeconds(delay);
        Resetter.Reset();
    }

    IEnumerator ShowResults()
    {
        GameObject.Find("Character").GetComponent<Move>().enabled = false;

        yield return new WaitForSeconds(delay);

        main_section.transform.localScale = Vector3.zero;
        results_section.transform.localScale = Vector3.one;

        float time = Time.realtimeSinceStartup - (start_time + delay);
        time = Mathf.Round((time * 10.0f)) / 10.0f;
        Text results = results_obj.transform.GetChild(0).GetComponent<Text>();
        results.text = results.text.Replace("XXXX", time.ToString());

        string levelStr = SceneManager.GetActiveScene().name;
        levelStr = levelStr.Replace("Level", "");
        int levelNum = int.Parse(levelStr);
        Unlocks.level_done[levelNum] = true;
    }

    private int NumCollected()
    {
        GameObject[] c = GameObject.FindGameObjectsWithTag("Collectable");
        return c.Length;
    }
}

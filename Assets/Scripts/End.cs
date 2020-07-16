using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class End : MonoBehaviour
{
    private int numLevels = 10;

    public AudioSource Cheer;
    public AudioSource Aww;

    private float delay = 1.5f;

    // Start is called before the first frame update
    void Start()
    {
        
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
                GetComponent<MeshRenderer>().enabled = false;
                StartCoroutine("NextLevel");
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

    IEnumerator NextLevel()
    {
        GameObject.Find("Character").GetComponent<Move>().enabled = false;
        yield return new WaitForSeconds(delay);
        string levelStr = SceneManager.GetActiveScene().name;
        levelStr = levelStr.Replace("Level", "");
        int levelNum = int.Parse(levelStr);
        string levelName = "Level" + (levelNum + 1).ToString();
        if (levelNum < numLevels)
        {
            SceneManager.LoadScene(levelName);
        }
        else
        {
            SceneManager.LoadScene("LevelSelect");
        }
    }

    private int NumCollected()
    {
        GameObject[] c = GameObject.FindGameObjectsWithTag("Collectable");
        return c.Length;
    }
}
